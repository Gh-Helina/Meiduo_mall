import base64
import json
import pickle
import re

from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.carts.utils import merge_cart_cookie_to_redis
from apps.goods.models import SKU
from apps.users.models import User, Address
from apps.users.utils import generic_active_email_url, check_active_token
from apps.verifications.constants import SMS_CODE_EXPIRES_SECONDS, SMS_FLAG_CODE_EXPIRES_SECONDS
from utils.response_code import RETCODE
from utils.users import logger


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 1.接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        # 2.验证数据
        # 2.1 四个参数必须都有值
        if not all([username, password, password2, mobile]):
            return HttpResponseBadRequest('参数不全')
        # 2.2 判断用户名是否符合规则，是否重复
        if not re.match(r'^[a-zA-Z0-9]{5,20}$', username):
            return HttpResponseBadRequest('用户名格式不符合')
        # 2.3 判断密码格式
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return HttpResponseBadRequest('密码格式不正确')
        # 2.4 确认密码和密码一致
        if password != password2:
            return HttpResponseBadRequest('密码不一致')
        # 2.5 手机号格式，是否重复
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式不正确')
        # 3.保存数据
        user = User.objects.create_user(username=username,
                                        password=password,
                                        mobile=mobile)

        # #########注册成功直接登录跳转到首页###########
        #         保持状态
        from django.contrib.auth import login
        # user用户对象上面接收保存数据的变量
        login(request, user)
        # 注册成功后跳转首页 重定向
        return redirect('contents:index')
        #     4.返回响应
        # return HttpResponse('注册成功')

    '''
    前端获取用户名需要发送ajax数据给后端
    后端判断用户名重复
    '''


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        # 获取前端提交数据
        # 查看数量 1重复,0不重复
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count': count})


class MobilCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': count})


#############用户登录####################
class LoginVies(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 1.获取数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        rememberd = request.POST.get('remembered')

        # 2. 验证数据
        if not all([username, password]):
            return HttpResponseBadRequest('参数不全')

        # 3.判断用户名密码是否一致
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')

        # 4. 状态保持
        login(request, user)

        # 5.记住登录
        if rememberd == 'on':
            # 记住登录，俩周后失效
            request.session.set_expiry(None)
        else:
            # 不记住登录，关闭浏览器失效
            request.session.set_expiry(0)
            # return redirect(reverse('contents:index'))

        ##############首页用户名展示#######################
        # 响应注册结果
        response = redirect(reverse('contents:index'))

        # 设置cookie
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # #合并购物车
        response = merge_cart_cookie_to_redis(request=request, user=user, response=response)
        return response


#
#     """
# 1.功能分析
#     用户行为:  点击退出按钮
#     前端行为:  前端发送请求
#     后端行为:  实现退出功能
#
# 2. 分析后端实现的大体步骤
#         ① 清除状态保持的信息
#         ② 跳转到指定页面
#
# 3.确定请求方式和路由
#     GET logout
# """
#
class LogoutView(View):
    #
    def get(self, request):
        #
        #         # request.session.flush()
        #
        from django.contrib.auth import logout
        logout(request)
        #
        #         #删除cookie中的username
        #         return redirect(reverse('contents:index'))
        response = redirect(reverse('contents:index'))
        #
        #         # response.set_cookie('username',None,max_age=0)
        response.delete_cookie('username')
        #
        return response

        ###########判断是否登录############
        # class UserCenterInfoView(View):
        #     def get(self,request):
        #       request.user 请求中 有用户的信息
        # is_authenticated 判断用户是否为登陆用户
        # 登陆用户为True
        # 未登陆用户为False
        # if request.user.is_authenticated:
        #     return render(request,'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))


# return render(request,'user_center_info.html')
# 第二种
from django.contrib.auth.mixins import LoginRequiredMixin


class UserCenterInfoView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_info.html')

    #########用户中心代码###############
    def get(self, request):
        # 1.获取用户登录信息
        context = {'username': request.user.username,
                   'mobile': request.user.mobile,
                   'email': request.user.email,
                   'email_active': request.user.email_active,
                   }
        # 2.传递模型进行渲染
        return render(request, 'user_center_info.html', context=context)


############邮件验证##########
# 必须登录用户,所以继承LoginRequiredMixin
class EmailView(LoginRequiredMixin, View):
    def put(self, request):
        # 1.接收  axios
        body = request.body
        body_str = body.decode()
        # 导入系统json，最后一个json
        data = json.loads(body_str)

        # 2.验证
        email = data.get('email')
        if not email:
            return HttpResponseBadRequest('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '邮箱不符合规则'})
        # 3.更新数据
        request.user.email = email
        request.user.save()
        # 4.给邮箱发送激活链接
        # 导入服务器
        # from django.core.mail import send_mail
        # subject, message, from_email, recipient_list,
        # subject        主题
        # subject = 'Forever激活邮件'
        # # message,       内容
        # message = ''
        # # from_email,  谁发的
        # from_email = '小姐姐<hln1369471@163.com>'
        # # recipient_list,  收件人列表
        # recipient_list = ['helina0329@163.com']
        # # 用户点击链接，，跳转到激成功页面，同时修改用户邮件状态
        #
        # # 对用户加密
        # active_url=generic_active_email_url(request.user.id,request.user.email)
        # # html_mesage = "<a href='http://www.meiduo.site:8000/emailactive/'>戳我有惊喜</a>"
        # html_mesage = "<a href='%s'>戳我有惊喜</a>"%active_url
        #
        # send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list, html_message=html_mesage)

        # 任务名.delay 添加到中间人
        from celery_tasks.email.tasks import send_active_email
        send_active_email.delay(request.user.id, email)

        # 5.返回响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


###########激活邮件####################
class EmailActiveView(View):
    def get(self, request):
        # 1.获取token
        token = request.GET.get('token')
        if token is None:
            return HttpResponseBadRequest('缺少参数')
        # 2.token信息解密
        data = check_active_token(token)
        if data is None:
            return HttpResponseBadRequest('验证失败')
        # 3.根据用户信息进行数据更新
        id = data.get('id')
        email = data.get('email')
        # 4.查询用户
        try:
            user = User.objects.get(id=id, email=email)
        except User.DoesNotExist:
            return HttpResponseBadRequest('验证失败')
        # 设置邮件激活状态
        user.email_active = True
        user.save()
        # 5.跳转到个人中心页面
        return redirect(reverse('users:center'))
        # return HttpResponse('激活成功')


############省市区渲染###############
class UserCentSiteView(View):
    def get(self, request):
        return render(request, 'user_center_site.html')


##############增加用户地址#######################
class CreateAddressView(LoginRequiredMixin, View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""
        # 判断是否超过地址上限：最多20个
        # Address.objects.filter(user=request.user).count()
        count = request.user.addresses.count()
        if count >= 20:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseBadRequest('参数email有误')

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


##############显示用户地址#######################
class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""
        # 获取用户地址列表
        login_user = request.user
        addresses = Address.objects.filter(user=login_user, is_deleted=False)

        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

        context = {
            'default_address_id': login_user.default_address_id,
            'addresses': address_dict_list,
        }

        return render(request, 'user_center_site.html', context)


##################修改地址#####################
class UpdateDestroyAddressView(LoginRequiredMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseBadRequest('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        # 响应更新地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


################设置默认地址地址#########################


class DefaultAddressView(LoginRequiredMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


####################修改地址标题#############################
class UpdateTitleAddressView(LoginRequiredMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


##############修改密码#######################
class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        # 1.接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        # 2.验证参数
        if not all([old_password, new_password, new_password2]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return HttpResponseBadRequest('密码最少8位，最长20位')
        if new_password != new_password2:
            return HttpResponseBadRequest('两次输入的密码不一致')

        # 3.检验旧密码是否正确
        if not request.user.check_password(old_password):
            return render(request, 'user_center_pass.html', {'origin_password_errmsg': '原始密码错误'})
        # 4.更新新密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_password_errmsg': '修改密码失败'})
        # 5.退出登陆,删除登陆信息
        logout(request)
        # 6.跳转到登陆页面
        response = redirect(reverse('users:login'))

        response.delete_cookie('username')

        return response


###########浏览记录###########
class UserBrowseHistory(LoginRequiredMixin, View):
    """用户浏览记录"""

    def post(self, request):
        # ①有用户信息(必须是登陆用户)
        user = request.user
        # ②获取商品id
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        # ③判断商品id(查询)
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此商品'})
        # 链接数据库
        redis_con = get_redis_connection('history')
        # 1.
        # 创建管道实例
        pipeline = redis_con.pipeline()
        # 2.
        # 管道收集指令
        # 去重
        # redis_con.lrem(key,count,value)
        pipeline.lrem('history_%s' % user.id, 0, sku_id)
        # 4.2 再添加
        pipeline.lpush('history_%s' % user.id, sku_id)
        # 4.3 确保有5条记录
        pipeline.ltrim('history_%s' % user.id, 0, 4)
        # 三,执行 !!!! 一定要记得执行
        pipeline.execute()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        # 去重
        # redis_con.lrem(key,count,value)
        # redis_con.lrem('history_%s' % user.id, 0, sku_id)
        # # 添加
        # redis_con.lpush('history_%s' % user.id, sku_id)
        # # 确保5条数据
        # redis_con.ltrim('history_%s' % user.id, 0,4)
        #
        # return JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

    def get(self, request):

        # ①获取用户信息
        user = request.user
        # ②获取redis数据 [16,10,1]
        redis_conn = get_redis_connection('history')
        ids = redis_conn.lrange('history_%s' % user.id, 0, 4)

        history_list = []
        for id in ids:
            # ③ 根据id查询商品详细信息 SKU
            sku = SKU.objects.get(id=id)
            # ④ 将对象转换为字典
            history_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        # ⑤ 返回数据
        # skus在js里 this.histories = response.data.skus;
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'skus': history_list})


#############忘记密码#################
class FindPwd(View):
    def get(self, request):
        return render(request, 'find_password.html')


# 第一步表单提交, 获取手机号 与  发送短信的token
class AouthView(View):
    def get(self, request, username):
        # 1.获取图片验证码
        uuid = request.GET.get('image_code_id')
        image_code = request.GET.get('text')
        # 获取redis中的图片
        redis_con = get_redis_connection('code')
        image_code_id = redis_con.get('image_%s' % uuid)
        # 判断
        if image_code_id is None:
            return HttpResponseBadRequest('图片验证码已过期')
        # 数据库删除uuid
        redis_con.delete(uuid)
        # 比对数据
        # 用户用小写
        if image_code_id.decode().lower() != image_code.lower():
            return HttpResponseBadRequest('图片验证码不一致')
        # 判断用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '此用户不存在'})
        # access_token = {'mobile': user.mobile, 'user_id': user.id, }
        access_token = base64.b64encode(pickle.dumps({'mobile': user.mobile, 'user_id': user.id})).decode()
        return JsonResponse({'mobile': user.mobile, 'access_token': access_token})


# 第二步 发送短信验证码
class PwdSmsView(View):
    def get(self, request):
        access_token = request.GET.get('access_token')
        user_dict = pickle.loads(base64.b64decode(access_token))
        # 判断
        if user_dict is None:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '验证信息已失效'})
        mobile = user_dict['mobile']
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            return JsonResponse({'code': RETCODE.MOBILEERR, 'errmsg': '手机号错误'})
        # 链接数据库
        redis_con = get_redis_connection('code')
        send_flag = redis_con.get('send_flag_%s' % mobile)
        if send_flag:
            return JsonResponse({'errmsg': '发送太频繁，稍后重试', 'code': RETCODE.THROTTLINGERR})
        # 生成随机短信验证码
        from random import randint
        sms_code = '%06d' % randint(0, 999999)
        print(sms_code)
        # 保存到redis
        # SMS_CODE_EXPIRES_SECONDS定义的变量在verifications/constants.py里，代表过期时间
        redis_con.setex('sms_%s' % mobile, SMS_CODE_EXPIRES_SECONDS, sms_code)
        # 添加一个标记
        redis_con.setex('send_flag_%s' % mobile, SMS_FLAG_CODE_EXPIRES_SECONDS, 1)
        from  celery_tasks.sms.tasks import send_sms_code
        # 任务.delay()    # 将celery添加到中间件
        send_sms_code.delay(mobile, sms_code)
        # 返回json，里面是字典形式
        return JsonResponse({'image': 'ok', 'code': RETCODE.OK})


# 第二步 表单提交，验证手机号，获取修改密码的access_token
class MobileCheckVIew(View):
    def get(self, request, username):
        # 获取短信验证码
        sms_code = request.GET.get('sms_code')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'code': RETCODE.USERERR, 'errmsg': '用户名错误'})
        # 短信验证码
        # 1.读取redis中的短信验证码
        redis_con = get_redis_connection('code')
        sms_code_redis = redis_con.get('sms_%s' % user.mobile)
        # 2.判断是否过期
        if sms_code_redis is None:
            return HttpResponseBadRequest('手机验证码已过期')
        # 3.删除短信验证码，不可以使用第二次
        redis_con.delete(user.mobile)
        redis_con.delete('sms_%s' % user.mobile)
        # 4.判断是否正确
        if sms_code_redis.decode() != sms_code:
            return HttpResponseBadRequest('验证码错误')
        # 字典转二进制字符串再编码
        access_token = base64.b64encode(pickle.dumps({'mobile': user.mobile, 'user_id': user.id})).decode()
        return JsonResponse({'user_id': user.id, 'access_token': access_token})


# 第三步 修改密码
class ChangePwd(View):
    def post(self, request, user_id):
        # 1.获取数据
        json_data = json.loads(request.body.decode())
        password = json_data.get('password')
        password2 = json_data.get('password2')
        access_token = json_data.get('access_token')
        # 2.判断数据
        if not all([password, password2, access_token]):
            return HttpResponseBadRequest('缺少参数')
        if password != password2:
            return HttpResponseBadRequest('密码不一致')
        # 3.对access_token解码转换为字典
        user_dict = pickle.loads(base64.b64decode(access_token))
        if user_dict is None:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '无匹配参数'})
            # return JsonResponse({}, status=400)
        if int(user_id) != user_dict['user_id']:
            return JsonResponse({'code':RETCODE. USERERR,'errmsg':'无此用户'})
            # return JsonResponse({}, status=400)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'code': RETCODE.USERERR, 'errmsg': '用户id不存在'})
            # return JsonResponse({}, status=400)
        # 4.保存密码
        user.set_password(password)
        user.save()
        return JsonResponse({'code':RETCODE.OK,'errmsg':0})
        # return JsonResponse({})

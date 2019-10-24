import json
import re

from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View

from apps.users.models import User, Address
from apps.users.utils import generic_active_email_url, check_active_token
from utils.response_code import RETCODE
from utils.users import logger


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    # 后台功能步骤
    def post(self, request):
        #     1.接受数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        #     2.验证数据
        # 2.1 四个参数都有值
        if not all([username, password, password2, mobile]):
            return HttpResponseBadRequest('参数不全')
        # 2.2 判断用户名是否符合规则,是否重复
        if not re.match(r'^[a-zA-Z0-9]{5,20}$', username):
            return HttpResponseBadRequest('用户名不满足要求')
        # 2.3 判断密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码格式不正确')
        # 2.4 判断确认密码和密码一致
        if password2 != password:
            return HttpResponseBadRequest('密码不一致')
        # 2.5 判断手机号格式及重复
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号格式错误')
        # 3.保存数据
        # 导入User 先输入导入
        user = User.objects.create_user(username=username,
                                        password=password,
                                        mobile=mobile)
        '''
           注册成功后直接登录跳转到首页
           '''
        # 状态保持
        from django.contrib.auth import login
        # user用户对象  上面接收保存数据的变量
        login(request, user)
        return redirect(reverse('contents:index'))
        #     4.返回响应
        return HttpResponse('注册成功')

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

        #任务名.delay 添加到中间人
        from celery_tasks.email.tasks import send_active_email
        send_active_email.delay(request.user.id,email)

        # 5.返回响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

###########激活邮件####################
class EmailActiveView(View):
    def get(self,request):
        # 1.获取token
        token=request.GET.get('token')
        if token is None:
            return HttpResponseBadRequest('缺少参数')
        # 2.token信息解密
        data = check_active_token(token)
        if data is None:
            return HttpResponseBadRequest('验证失败')
        # 3.根据用户信息进行数据更新
        id=data.get('id')
        email = data.get('email')
        # 4.查询用户
        try:
            user=User.objects.get(id=id,email=email)
        except User.DoesNotExist:
            return HttpResponseBadRequest('验证失败')
        #设置邮件激活状态
        user.email_active=True
        user.save()
        # 5.跳转到个人中心页面
        return redirect(reverse('users:center'))
        # return HttpResponse('激活成功')

############省市区渲染###############
class UserCentSiteView(View):
    def get(self,request):
        return render(request,'user_center_site.html')


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
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
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
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address':address_dict})




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
                "province_id":address.province_id,
                "city": address.city.name,
                "city_id":address.city_id,
                "district": address.district.name,
                "district_id":address.district_id,
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
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
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
            return render(request, 'user_center_pass.html', {'origin_password_errmsg':'原始密码错误'})
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
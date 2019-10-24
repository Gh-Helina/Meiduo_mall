import re
from django.contrib.auth.views import login
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import serect_openid, check_openid

from meiduo_mall import settings


class QQLoginView(View):
    def get(self, request):
        # 1.获取code
        code = request.GET.get('code')
        state = request.GET.get('state')
        # 判断是否有code
        if code is None:
            return HttpResponseBadRequest('NO Code')
        # 2.通过code换取token  跳转到oatuh_callback
        from QQLoginTool.QQtool import OAuthQQ
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=state)
        token = oauth.get_access_token(code)
        # 3.获取openid
        openid = oauth.get_open_id(token)
        # return render(request, 'oauth_callback.html')
        # 4. 根据openid数据查询判断
        #   4.1 如果存在就登录
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:

            # 如果数据库中不存在了openid,说明用户没有绑定过了,我们应该让他绑定
            return render(request, 'oauth_callback.html', context={'openid': openid})
        else:
            # 如果数据库中已经存在了openid,说明用户已经绑定过了,我们应该让它登陆

            # 保持登陆的状态
            login(request, qquser.user)

            response = redirect(reverse('contents:index'))
            # 设置cookie
            response.set_cookie('username', qquser.user.username, max_age=24 * 3600)

            return response

    def post(self, request):
        """美多商城用户绑定到openid"""
        # ①接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('pwd')
        # pic_code = request.POST.get('pic_code')
        sms_code = request.POST.get('sms_code')
        secret_openid = request.POST.get('openid')

        # ②验证数据
        # #  参数是否齐全
        # if not all([mobile, password,  sms_code]):
        #     return HttpResponseBadRequest('参数不全')

        # 手机号是否符合规则
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     return HttpResponseBadRequest('请输入正确的手机号')

        # 密码是否符合规则
        # if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
        #     return HttpResponseBadRequest('请输入8-20位的密码')

        # 短信验证码是否一致
        # from django_redis import get_redis_connection
        # redis_conn = get_redis_connection('code')
        # sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 没有短信验证码
        # if sms_code_server is None:
        #     return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})
        #
        # 获取到的密码与数据库密码不相等
        # if sms_code != sms_code_server:
        #     return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})
        #
        # openid解密
        openid = check_openid(secret_openid)
        if openid is None:
            return HttpResponseBadRequest('openid错误')

        # ③根据手机号进行用户信息的查询  user
        try:
            from apps.users.models import User
            user = User.objects.get(mobile=mobile)

        except User.DoesNotExist:
            #   如果不存在,说明用户手机号没有注册过,我们就以这个手机号注册一个用户
            user = User.objects.create(username=mobile, password=password, mobile=mobile)

            # 创建完并加密
            new_openid = serect_openid(openid)
            # 运行登录检查里会看到加密后的openid
            # value = "eluqnHjkip6zNjyXf3L2QWXTfcoGhpaf3Nhw71tWZoIiNQeT1zYtEr0DPkcck8mY"

        else:
            #    如果存在,则需要验证密码
            from apps.users.models import User
            # 状态保持
            login(request, user)
            if user.check_password(password):
                return HttpResponseBadRequest('密码错误')

                # ④ 绑定openid 和 user
                #user新创的=user
        OAuthQQUser.objects.create(user=user, openid=secret_openid)
        # ⑤ 登陆(设置登陆状态,设置cookie,跳转到首页)
        login(request, user)

        response = redirect(reverse('contents:index'))

        response.set_cookie('username', user.username, max_age=24 * 3600)

        return response

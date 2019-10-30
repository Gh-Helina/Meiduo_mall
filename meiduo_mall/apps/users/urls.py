from django.conf.urls import url
from . import views

urlpatterns = [
    # 注册用户
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    # 登录用户
    url(r'^login/$', views.LoginVies.as_view(), name='login'),
    # 退出用户
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # 是否登录
    url(r'^center/$', views.UserCenterInfoView.as_view(), name='center'),
    # 邮箱验证
    url(r'^emails/$', views.EmailView.as_view(), name='email'),
    # 发送验证
    url(r'^emailsactive/$', views.EmailActiveView.as_view(), name='emailsactive'),
    # 省市区
    url(r'^site/$', views.UserCentSiteView.as_view(), name='address'),
    # 新增地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view(), name='addresses/create'),
    # 修改地址
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view(), name='addresses/update'),
    # 默认
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view(), name='addresses/default'),
    # 标题
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.DefaultAddressView.as_view(), name='addresses/title'),
    # 修改密码
    url(r'^password/$', views.ChangePasswordView.as_view(), name='password'),
    # 浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistory.as_view(), name='history/'),
    # 判断用户是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/$', views.UsernameCountView.as_view(), name='usernamecount'),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/$', views.MobilCountView.as_view(), name='mobilecount'),
    # 忘记密码
    # 找回密码页面
    url(r'^find_password/$', views.FindPwd.as_view(), name='find_pwd'),
    # 第一步表单提交, 获取手机号 与  发送短信的token
    url(r'^accounts/(?P<username>\w+)/sms/token/$', views.AouthView.as_view(), name='AouthView'),
    # 第二步 发送短信验证码
    url(r'^sms_codes/$', views.PwdSmsView.as_view(), name='sms_codes'),
    # 第二步 表单提交，验证手机号，获取修改密码的access_token
    url(r'^accounts/(?P<username>\w+)/password/token/$', views.MobileCheckVIew.as_view(), name='passwordtoken'),

    url(r'^users/(?P<user_id>\d+)/password/$', views.ChangePwd.as_view(), name='changepassword'),
]

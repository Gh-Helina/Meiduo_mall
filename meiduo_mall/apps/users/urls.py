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
    #邮箱验证
    url(r'^emails/$', views.EmailView.as_view(), name='email'),
    #发送验证
    url(r'^emailsactive/$', views.EmailActiveView.as_view(), name='emailsactive'),
    #省市区
    url(r'^site/$', views.UserCentSiteView.as_view(), name='site'),
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
    # 判断用户是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/$', views.UsernameCountView.as_view(), name='usernamecount'),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/$', views.MobilCountView.as_view(), name='mobilecount'),
]

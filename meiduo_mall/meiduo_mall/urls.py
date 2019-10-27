"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
#测试日志
from django.http import HttpResponse


def test(request):
    # 1.导入日志包
    import logging
    # 2. 创建/获取
    logger=logging.getLogger('django')
    # 3. 根据日志等级来记录日志
    logger.error('Error')
    logger.info('Yes')
    logger.warning('119')
    return HttpResponse('ha')
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(r'test/$',test),
    url(r'^',include(('apps.users.urls','apps.users'),namespace='users')),
    # 跳转首页
    url(r'^',include(('apps.contents.urls','apps.contents'),namespace='contents')),
    # 图片验证
    url(r'^',include(('apps.verifications.urls','apps.verifications'),namespace='verifications')),
    #QQ登录
    url(r'^',include(('apps.oauth.urls','apps.oauth'),namespace='oauth')),
    #省市区
    url(r'^',include(('apps.areas.urls','apps.areas'),namespace='areas')),
    #购物车
    url(r'^',include(('apps.carts.urls','apps.carts'),namespace='carts')),

    url(r'^',include(('apps.goods.urls','apps.goods'),namespace='goods')),
    #支付
    url(r'^',include(('apps.orders.urls','apps.orders'),namespace='orders')),
]

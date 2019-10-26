from django.conf.urls import url
from . import views
urlpatterns = [
    #购物车增删改查
    url(r'^carts/$',views.CartsView.as_view(),name='carts'),
    #全选
    url(r'^carts/selection/$',views.CartsSelectAllView.as_view(),name='carts/selection'),
    #展示商品页面简单购物车#
    url(r'^carts/simple/$',views.CartsSimpleView.as_view(),name='carts/simple'),
]
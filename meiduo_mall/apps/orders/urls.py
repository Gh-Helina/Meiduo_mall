from django.conf.urls import url
from . import views
urlpatterns = [
    #订单显示
    url(r'^placeorder/',views.PlaceOrderView.as_view(),name='placeorder'),
    #订单提交
    url(r'^orders/commit/',views.OrderCommitView.as_view(),name='orderscommit'),
    #提交成功
    url(r'^orders/success/',views.OrderSuccessView.as_view(),name='orderssuccess'),

]
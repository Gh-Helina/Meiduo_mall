from django.conf.urls import url
from . import views
urlpatterns = [
    #订单支付
    url(r'^payment/(?P<order_id>\d+)/',views.PaymentView.as_view(),name='payment'),
    #保存订单结果
    url(r'^payment/status/',views.PaymentStatusView.as_view(),name='paymentstatus'),
    # 我的订单
    # url(r'^payment/(?P<order_id>\d+)/',views.Mypayment.as_view(),name='paymentstatususer'),
]
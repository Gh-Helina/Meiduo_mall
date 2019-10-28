from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
# 测试账号：axirmj7487@sandbox.com
from django.views import View

from apps.orders.models import OrderInfo
from utils.response_code import RETCODE


class PaymentView(LoginRequiredMixin, View):
    """订单支付功能"""

    def get(self, request, order_id):
        # 1.获取订单id
        try:
        # 为了让查询更准确
            order=OrderInfo.objects.get(order_id=order_id,
                                        user=request.user,
                                        status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此订单'})
        # 2.创建alipay实例对象
        from alipay import AliPay
        from meiduo_mall import settings
        # 读取私钥和公钥
        app_private_key_string=open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string=open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        alipay=AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 3.调用网站支付方式,生成order_string
        subject = "测试订单"

        # 线上 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # decimal
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL,
            # notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
        )
        # 4.拼接url
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # ⑤返回相应 支付的url
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'alipay_url': alipay_url})


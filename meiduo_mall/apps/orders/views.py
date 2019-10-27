from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.users.models import Address


class PlaceOrderView(LoginRequiredMixin, View):
    def get(self, request):
        # 1.必须是登录用户才可以展示
        user=request.user
        # 2.获取登录用户地址信息
        address=Address.objects.filter(user=user,is_deleted=False)
        # 3.用户redis中选中的商品信息
        #     3.1 链接数据库
        redis_con=get_redis_con
        #     3.2 获取hash
            # set
        # 将bytes转换
        # 转换过程中只获取选中的字典
        # 4.根据商品信息，获取商品详细信息
        # 运费

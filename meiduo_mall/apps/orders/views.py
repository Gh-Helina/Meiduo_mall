from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import Address


# class PlaceOrderView(LoginRequiredMixin, View):
#     def get(self, request):
#         # 1.必须是登录用户才可以展示
#         user = request.user
#         # 2.获取登录用户地址信息
#         address = Address.objects.filter(user=user, is_deleted=False)
#         # 3.用户redis中选中的商品信息
#         #     3.1 链接数据库
#         redis_con = get_redis_connection('carts')
#         #     3.2 获取hash
#         hash_id_cart = redis_con.hgetall('carts_%s' % user.id)
#         # set
#         set_cart_selected = redis_con.smembers('selected_%s' % user.id)
#         selected_dict = {}
#         # 判断如果id在选择里
#         for id in set_cart_selected:
#             # 转换为cookie格式
#             selected_dict[int(id)] = int(hash_id_cart[id])
#             # 转换过程中只获取选中的字典
#             # 4.根据商品信息，获取商品详细信息
#             ids = selected_dict.keys()
#             skus = []
#             total_count = 0
#             total_amount = 0
#             for id in ids:
#                 sku = SKU.objects.get(id=id)
#                 sku.count = selected_dict[id]  # 数量
#                 sku.amout = (sku.price * sku.count)  # 小计  price*count
#                 skus.append(sku)
#                 # 累加计算
#                 # 计算总数量和总金额
#                 total_count += sku.count
#                 total_amount += sku.count * sku.price
#
#             # 运费
#             freight = Decimal('10.00')
#             context = {
#                 'addresses': address,
#                 'skus': skus,
#                 'total_count': total_count,
#                 'total_amount': total_amount,
#                 'freight': freight,
#                 'payment_amount': total_amount + freight
#             }
#             return render(request, 'place_order.html', context=context)
from django.shortcuts import render

# Create your views here.
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import Address


class PlaceOrderView(LoginRequiredMixin,View):

    def get(self,request):
        # 1.必须是登陆用户才可以展示
        user=request.user
        # 2.获取登陆用户的地址信息
        addresses=Address.objects.filter(user=user,is_deleted=False)

        # 3.获取登陆用户redis中,选中的商品信息
        redis_conn = get_redis_connection('carts')

        #hash  {sku_id:count}
        id_counts=redis_conn.hgetall('carts_%s'%user.id)
        #set
        selected_ids=redis_conn.smembers('selected_%s'%user.id)

        #将bytes类型进行转换
        #在转换过程中,我们最终只组织一个选中的字典
        # selected_dict = {sku_id:count}
        selected_dict={}
        for id in selected_ids:
            selected_dict[int(id)]=int(id_counts[id])

        # 4.根据商品信息,回去商品详细信息
        ## selected_dict = {sku_id:count}
        ids=selected_dict.keys()
        # skus=SKU.objects.filter(id__in=ids)

        skus=[]
        # 准备初始值
        total_count = 0
        total_amount = 0
        for id in ids:
            sku=SKU.objects.get(id=id)
            sku.count=selected_dict[id]   #数量
            sku.amount=(sku.price*sku.count) #小计
            skus.append(sku)
            #累加计算
            total_count+=sku.count
            total_amount+=sku.amount

        #运费
        freight=10

        context = {
            'addresses':addresses,
            'skus':skus,

            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount':total_amount + freight
        }

        return render(request,'place_order.html',context=context)
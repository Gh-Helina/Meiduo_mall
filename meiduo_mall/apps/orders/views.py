import json

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.response_code import RETCODE


class PlaceOrderView(LoginRequiredMixin, View):
    def get(self, request):
        """
        1.这个视图必须是登陆用户才可以展示
        2.获取登陆用户的地址信息
        3.获取登陆用户redis中,选中的商品信息
        4.根据商品信息,回去商品详细信息
        """
        # 1.这个视图必须是登陆用户才可以展示
        user = request.user
        # 2.获取登陆用户的地址信息
        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 3.获取登陆用户redis中,选中的商品信息
        redis_conn = get_redis_connection('carts')

        # hash  {sku_id:count}
        id_counts = redis_conn.hgetall('carts_%s' % user.id)
        # set
        selected_ids = redis_conn.smembers('selected_%s' % user.id)

        # 将bytes类型进行转换
        # 在转换过程中,我们最终只组织一个选中的字典
        # selected_dict = {sku_id:count}
        selected_dict = {}
        for id in selected_ids:
            selected_dict[int(id)] = int(id_counts[id])

        # 4.根据商品信息,回去商品详细信息
        ## selected_dict = {sku_id:count}
        ids = selected_dict.keys()
        # skus=SKU.objects.filter(id__in=ids)

        skus = []
        # 准备初始值
        total_count = 0
        total_amount = 0
        for id in ids:
            sku = SKU.objects.get(id=id)
            sku.count = selected_dict[id]  # 数量
            sku.amount = (sku.price * sku.count)  # 小计
            skus.append(sku)
            # 累加计算
            total_count += sku.count
            total_amount += sku.amount

        # 运费
        freight = 10

        context = {
            'addresses': addresses,
            'skus': skus,
            # 以下的几个 复制过来
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }

        return render(request, 'place_order.html', context=context)


class OrderCommitView(LoginRequiredMixin, View):
    def post(self, request):
        # 接收数据
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        pay_method = data.get('pay_method')
        # 验证数据
        if not all([address_id, pay_method]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})
        # 数据入库
        #     1 先写入订单基本信息
        #         1.1 获取用户信息
        user = request.user
        #         1.2 获取地址信息
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '地址不正确'})
        # 1.3  order_id   年月日时分秒+9位用户id
        from django.utils import timezone

        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        #         1.4  总数量(0),总金额(0),运费
        total_count = 0  # 总数量
        from decimal import Decimal
        total_amount = Decimal('0')  # 总金额
        freight = Decimal('10.00')  # 运费

        # 增加了代码的可读性
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '支付方式错误'})
        # 1.6  支付状态 由支付方式决定
        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            # 现金支付
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            # 支付宝
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        from django.db import transaction
        # with 语句就是针对于特定(部分)代码进行事务
        with transaction.atomic():

            # ① 创建事务的保存点
            savepoint = transaction.savepoint()
            try:
                order_info = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=total_count,
                    total_amount=total_amount,
                    freight=freight,
                    pay_method=pay_method,
                    status=status
                )

                #     2 再写入订单商品信息
                #         2.1 获取redis中,指定用户的选中信息 [1,2]
                redis_conn = get_redis_connection('carts')
                id_counts = redis_conn.hgetall('carts_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)

                # 选中商品的id
                # selected_dict
                selected_dict = {}
                for id in selected_ids:
                    selected_dict[int(id)] = int(id_counts[id])

                # selected_dict = {sku_id:count,sku_id:count,....}

                #         2.2 根据id查询商品信息
                for sku_id, count in selected_dict.items():
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        #         2.3 判断商品库存是否充足
                        if sku.stock < count:
                            # 说明库存不足
                            # ② 回滚
                            transaction.savepoint_rollback(savepoint)

                            return JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # 2.4 商品库存减少,销量增加

                        # 乐观锁
                        # 乐观锁 第一步,先记录库存
                        old_stock = sku.stock
                        # 乐观锁 第二步 计算更新后的数据
                        new_stock = sku.stock - count
                        new_sales = sku.sales + count
                        # 更新前,再判断一次,相同则更新数据
                        # 乐观所 第三步,更新前,再判断一次,相同则更新数据
                        rect = SKU.objects.filter(id=sku_id, stock=old_stock).update(stock=new_stock, sales=new_sales)

                        if rect == 0:
                            continue
                            # 说明修改失败
                            transaction.savepoint_rollback(savepoint)
                            return JsonResponse({'code':RETCODE.STOCKERR,'errmsg':'下单失败'})

                        #         2.5 将商品信息写入到订单商品信息表中
                        OrderGoods.objects.create(
                            order=order_info,
                            sku=sku,
                            count=count,
                            price=sku.price
                        )
                        #         2.6 累加计算,总数量和总金额
                        order_info.total_count += count
                        order_info.total_amount += (count * sku.price)
                        break
                #
                #     3.更新订单基本信息中的总数量和总金额
                order_info.save()
            except Exception as e:
                transaction.savepoint_rollback(savepoint)
            else:
                # ③ 提交
                transaction.savepoint_commit(savepoint)

        # 4.选中的数据应该删除
        # redis_conn.hdel('carts_%s'%user.id,*selected_ids)
        # redis_conn.srem('selected_%s'%user.id,*selected_ids)
        # 返回响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok',
                             'order_id': order_info.order_id,
                             'payment_amount': order_info.total_amount,
                             'pay_method': order_info.pay_method})


class OrderSuccessView(View):
    def get(self, request):
        order_id = request.GET.get('order_id')
        pay_method = request.GET.get('pay_method')
        payment_amount = request.GET.get('payment_amount')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request, 'order_success.html', context=context)


# 返回相应
#
# 3.确定请求方式和路由
#     POST   commit/

###########显示支付成功页面#####################

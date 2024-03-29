# import json
#
# from django.http import JsonResponse
# from django.shortcuts import render
#
# # Create your views here.
# from django.views import View
# from django_redis import get_redis_connection
#
# from apps.goods.models import SKU
# from utils.response_code import RETCODE

"""

1. 如果用户未登录,可以实现添加购物车的功能.
   如果用户登录,也可以实现添加购物车的功能.

2.如果用户未登录, 我们要保存 商品id,商品数量,商品的选中状态
  如果用户登录, 我们要保存 用户id, 商品id,商品数量,商品的选中状态

3.如果用户未登录,  保存在 浏览器中   cookie中
  如果用户登录,    保存在数据库中   (为了让大家更好的学习redis)我们把数据保存到redis中


4. 如果用户未登录,  cookie的数据格式
    {
        sku_id:{count:5,selected:True},
        sku_id:{count:2,selected:False},
        sku_id:{count:7,selected:True},
    }

    如果用户登录, Redis  .Redis的数据是保存在内存中,
    我们要尽量少的占用内存空间

    user_id ,sku_id,count,selected

    1,          100,2,True
                101,5,False
                102,10,True
                103,10,False



    key         100:2
                selected_100:True

                101:5
                selected_101:False

                102:10
                selected_102:True

                103:10
                selected_103:False

            hash
    user_id     100:2
                101:5
                102:10
                103:10
            set  选中的在集合中
selected_user_id   [100,102]


                hash
    user_id     100:2
                101:-5
                102:10
                103:-10


5.

{
    sku_id:{count:5,selected:True},
    sku_id:{count:2,selected:False},
    sku_id:{count:7,selected:True},
}

base64


1G = 1024MB
1M=1024KB
1KB=1024B
1B=8bite 比特位  0  1

A   0100 0001

0100 0001   0100 0001   0100 0001
A               A           A


010000     010100   000101     000001
x               y    z          a


  5.1 将字典转换为二进制

  5.2 再进行base64编码

"""
import base64
from billiard.common import pickle

# class CartsView(View):
#     def post(self,request):
#         # 1.接收参数,验证参数
#         json_data=json.loads(request.body.decode())
#         sku_id=json_data.get('sku_id')
#         count=json_data.get('count')
#         selected=json_data.get('selected',True)
#         if not all([sku_id,count]):
#             return HttpResponseBadRequest('缺少必传参数')
#         # 判断sku_id是否存在
#         try:
#             SKU.objects.get(id=sku_id)
#         except SKU.DoesNotExist:
#             return HttpResponseBadRequest('商品id不存在')
#         # 判断count是否为数字
#         try:
#             count=int(count)
#         except Exception:
#             return HttpResponseBadRequest('参数count有误')
#         # 判断selected是否为bool值
#         if selected:
#             if not isinstance(selected, bool):
#                 return HttpResponseBadRequest('参数selected有误')
#
#         # 2.获取用户信息
#         user=request.user
#         # 3.判断用户登录状态
#         if user.is_authenticated:
#             # 4.根据是否登录判断登录用户
#             # 4.1链接数据库
#             # sittings里单独设置一个carts库
#             redis_conn = get_redis_connection('carts')
#             # 4.2操作数据库
#             # hash
#             # redis_conn.hset(hash_key,fiekd,value)
#             redis_conn.hset('carts_%s'%user.id,sku_id,count)
#             #set
#             # redis_conn.sadd key member
#             redis_conn.sadd('selected_%s'%user.id,sku_id)
#             return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
#         else:
#             #未登录
#             #先获取cookie，可能存在的
#             carts_str=request.COOKIES.get('cares')
#             if carts_str is None:
#                 # 不存在
#                 cookie_data = {
#                     sku_id: {'count': count, 'selected': True}
#                 }
#
#             else:
#                 # 存在  1.先解码
#                 decode_data=base64.b64decode(carts_str)
#                 #2.bytes转字典
#                 cookie_data=pickle.dump(decode_data)
#                 # 需要进行判断数量
#                 if sku_id in cookie_data:
#                 # 在累加数量
#                 # 先获取原来的
#                     origin_count=cookie_data[sku_id]['count']
#                     count+=origin_count
#                     cookie_data[sku_id]={'count':count,'selected':True}
#                 else:
#                     #创建一条记录
#                     cookie_data[sku_id]={'count':count,'selected':True}
#         #  字典转bytes
#             cookie_bytes = pickle.dumps(cookie_data)
#             #  base64编码
#             cookie_str = base64.b64encode(cookie_bytes)
#             #     5.3 设置cookie
#             response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
#
#             response.set_cookie('carts', cookie_str, max_age=7 * 24 * 3600)
#
#             #     5.4 返回相应
#             return response
import json

from django.http import HttpResponseBadRequest
from django.http import JsonResponse
# Create your views here.
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.carts.utils import merge_cart_cookie_to_redis
from apps.goods.models import SKU
from utils.response_code import RETCODE


class CartsView(View):
    """
    1.功能分析
    用户行为:
    前端行为:       当用户点击加入购物车的时候,前端要收集用户信息,sku_id,count,默认是选中
    后端行为:

    2. 分析后端实现的大体步骤

        1.接收数据,判断商品信息
        2.先获取用户信息
        3.根据用户是否登陆来判断
        4.登陆用户操作数据(redis)
            4.1 连接数据库
            4.2 操作数据库
            4.3 返回相应
        5.未登录用户操作cookie
            5.1 组织数据
            5.2 对数据进行编码
            5.3 设置cookie
            5.4 返回相应
        6.返回相应

    3.确定请求方式和路由
        POST        carts
    """

    # 添加购物车 #
    def post(self, request):

        # 1.接收数据,判断商品信息
        json_data = json.loads(request.body.decode())
        sku_id = json_data.get('sku_id')
        count = json_data.get('count')
        if not all([sku_id, count]):
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数不全'})
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此商品'})

        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': "参数错误"})
        # 添加购物车默认就是选中
        selected = True
        # 2.先获取用户信息
        user = request.user
        # 3.根据用户是否登陆来判断
        # is_authenticated 是认证用户(注册用户)
        if user.is_authenticated:
            # 4.登陆用户操作数据(redis)
            #     4.1 连接数据库
            redis_conn = get_redis_connection('carts')
            #     4.2 操作数据库
            # hash   key:
            #               sku_id:count
            #               field:value
            #               field:value

            # 累加hincrby 数量
            # redis_conn.hset('carts_%s' % user.id, sku_id, count)
            # 创建管道实例
            pl = redis_conn.pipeline()
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 收集数据
            # set
            pl.sadd('selected_%s' % user.id, sku_id)
            #     4.3 返回相应
            # 执行管道
            pl.execute()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        else:
            # 5.未登录用户操作cookie

            # 5.0 先获取cookie中 可能存在的数据
            carts_str = request.COOKIES.get('carts')
            if carts_str is None:
                # 说明没有购物车数据
                cookie_data = {
                    sku_id: {'count': count, 'selected': True}
                }
            else:
                # 说明有购物车数据
                # 先base64解码
                decode_data = base64.b64decode(carts_str)
                # 再bytes转字典
                cookie_data = pickle.loads(decode_data)
                # 再需要进行判断
                # {1:{count:5,selected:True}}
                # 商品id是否在字典中
                # 1
                if sku_id in cookie_data:

                    # 累加数量[1]['16']
                    origin_count = cookie_data[sku_id]['count']
                    # count=origin_count+count
                    count += origin_count
                    # 更新字典数据
                    cookie_data[sku_id] = {'count': count, 'selected': True}
                else:
                    cookie_data[sku_id] = {'count': count, 'selected': True}

            # 5.1 组织数据
            """
            {
                sku_id:{count:5,selected:True},
                sku_id:{count:2,selected:False},
                sku_id:{count:7,selected:True},
            }
            """

            #     5.2 对数据进行编码
            #  字典转bytes
            cookie_bytes = pickle.dumps(cookie_data)
            #  base64编码
            cookie_str = base64.b64encode(cookie_bytes)
            #     5.3 设置cookie
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

            response.set_cookie('carts', cookie_str, max_age=7 * 24 * 3600)

            #     5.4 返回相应
            return response


            #############展示购物车信息################

        # 显示购物车 #
    # 显示购物车 #
    def get(self, request):
        # 1.先获取用户
        user = request.user
        if user.is_authenticated:

            # 2.如果用户登陆,则从redis中获取信息
            #     2.1链接redis
            redis_conn = get_redis_connection('carts')
            #     3.2 获取redis数据
            #     hash    sku_id:count
            # {sku_id:count,sku_id:count,....}
            # {1:10,2:20}
            id_counts = redis_conn.hgetall('carts_%s' % user.id)
            #     set     [sku_id,sku_id]
            # [sku_id,sku_id]
            # [1]
            # 获取所有选中的成员
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            # 将redis数据转换为cookie格式
            #   cookie_str = {sku_id:{count:5,selected:True}}
            cookie_dict = {}
            for sku_id, count in id_counts.items():
                # if sku_id in selected_ids:
                #     selected=True
                # else:
                #     selected=False
                # sku_id in selected_ids如果商品id在选中的列表中那么就是选中的
                # redis数据是bytes类型,所以要转换数据类型
                cookie_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_ids
                }
        else:

            # 2.如果用户为登陆,则从cookie中获取信息
            #     {
            #         sku_id:{count:5,selected:True},
            #         sku_id:{count:2,selected:False},
            #         sku_id:{count:7,selected:True},
            #     }
            cookie_data = request.COOKIES.get('carts')
            if cookie_data is not None:
                # 先进行base64解码
                cookie_dict = pickle.loads(base64.b64decode(cookie_data))
            else:
                cookie_dict = {}
                # 4 获取商品id  -- 因为redis的数据结构和cookie的数据结构不一致
                # 我们应该让他们的数据一致
                #   cookie_dict = {
                #         sku_id:{count:5,selected:True},
                #         sku_id:{count:2,selected:False},
                #         sku_id:{count:7,selected:True},
                #     }
        ids = cookie_dict.keys()
        # 5 根据商品id进行商品信息的查询
        carts_list = []
        for id in ids:
            sku = SKU.objects.get(id=id)
            # 6 将对象转换为字典
            carts_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': cookie_dict.get(sku.id).get('count'),
                'selected': str(cookie_dict.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * cookie_dict.get(sku.id).get('count')),
            })
            # 7 返回响应
        return render(request, 'cart.html', context={'cart_skus': carts_list})

    # 修改购物车 #
    def put(self, request):
        """
            1.功能分析
                用户行为:       用户可能会点击某一个商品的数量/选中状态
                前端行为:       前端需要收集 点击的 sku_id,count,selected 以及用户信息
                后端行为:       实现更新

            2. 分析后端实现的大体步骤
                    1.接收数据
                    2.验证数据
                    3.获取用户信息
                    4.登陆用户更新redis
                        4.1 连接redis
                        4.2 更新数据
                        4.3 返回相应
                    5.未登录用户更新cookie
                        5.1 获取cookie中的数据,并进行判断
                            如果有数据则需要进行解码
                        5.2 更新数据  cart={}
                        5.3 将字典进行编码
                        5.4 设置cookie
                        5.5 返回相应

            3.确定请求方式和路由
            """
        # 1.接收收据
        json_data = json.loads(request.body.decode())
        sku_id = json_data.get('sku_id')
        count = json_data.get('count')
        selected = json_data.get('selected')
        # 2.验证数据
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此信息'})
            # 3.获取用户信息
        user = request.user
        if user.is_authenticated:

            # 4.登陆用户更新redis
            #     4.1 连接redis
            redis_con = get_redis_connection('carts')
            #     4.2 更新数据
            # hash
            redis_con.hset('carts_%s' % user.id, sku_id, count)
            # set
            if selected:
                redis_con.sadd('selected_%s' % user.id, sku_id)
            else:
                redis_con.srem('selected_%s' % user.id, sku_id)
                #     4.3 返回相应
            data = {
                'count': count,
                'id': sku_id,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': data})
        else:

            # 5.未登录用户更新cookie
            #     5.1 获取cookie中的数据,并进行判断
            cookie_str = request.COOKIES.get('carts')
            if cookie_str is not None:
                cookie_dict = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_dict = {}
                #     5.2 更新数据  cart={}
                # sku_id 是否在字典列表中
                # carts = {sku_id:{count:5,selected:True}}
            if sku_id in cookie_dict:
                cookie_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }
                #     5.3 将字典进行编码
                cookie_data = base64.b64encode(pickle.dumps(cookie_dict))
                #     5.4 设置cookie
                data = {
                    'count': count,
                    'id': sku_id,
                    'selected': selected,
                    'name': sku.name,
                    'default_image_url': sku.default_image.url,
                    'price': sku.price,
                    'amount': sku.price * count,
                }
                response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': data})
                response.set_cookie('carts', cookie_data, max_age=7 * 24 * 3600)

                # 5.5 返回相应

                return response

    # 删除购物车 #
    def delete(self, request):

        # 1.接收数据
        json_data = json.loads(request.body.decode())
        sku_id = json_data.get('sku_id')
        # 2.验证数据
        try:
            # sku=SKU.objects.get(id=sku_id)
            # pk primary key 主键
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此数据'})

        # 3.获取用户信息,并进行判断
        user = request.user
        if user.is_authenticated:
            # 4.登陆则操作redis
            #     4.1 连接redis
            redis_con = get_redis_connection('carts')
            #     4.2 hash
            redis_con.hdel('carts_%s' % user.id, sku_id)
            # set
            redis_con.srem('selected_%s' % user.id, sku_id)
            #     4.3 返回响应
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

        # 5.未登录则操作cookie
        else:
            #     5.1 先获取cookie数据,并进行判断
            cookie_str = request.COOKIES.get('carts')
            #         如果有数据,则进行解码
            if cookie_str is not None:
                cookie_dict = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_dict = {}

                #     5.2 删除数据  {}
            if sku_id in cookie_dict:
                del cookie_dict[sku_id]
                #     5.3 对数据进行编码
            cookie_data = base64.b64encode(pickle.dumps(cookie_dict))
            #     5.4 设置cookie数据
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
            response.set_cookie('carts', cookie_data, max_age=7 * 24 * 3600)
            #     5.5 返回相应
            return response


###############全选####################
class CartsSelectAllView(View):
    """全选购物车"""

    def put(self, request):
        # 接收和校验参数
        data = json.loads(request.body.decode())
        selected = data.get('selected')
        if selected:
            if not isinstance(selected, bool):
                return HttpResponseBadRequest('参数selected有误')
        # 判断用户是否登录
        user = request.user
        # 用户已登录，操作redis购物车
        if user.is_authenticated:
            redis_con = get_redis_connection('carts')
            cart = redis_con.hgetall('carts_%s' % user.id)
            sku_id_list = cart.keys()
            # 全选
            if selected:
                redis_con.sadd('selected_%s' % user.id, *sku_id_list)
            else:
                # 取消全选
                redis_con.srem('selected_%s' % user.id, *sku_id_list)
            return JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
        else:
            # 用户未登录，操作cookie购物车
            cart = request.COOKIES.get('carts')
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': '全选购物车成功'})
            if cart is not None:
                # 解码为二进制转换为字典
                cart = pickle.loads(base64.b64decode(cart.encode()))
                for sku_id in cart:
                    cart[sku_id]['selected'] = selected
                    # 字典转换为二进制进行编码
                cookie_cart = base64.b64encode(pickle.dump(cart)).decode()
                response.set_cookie('carts', cookie_cart, max_age=24 * 3600)
            return response


##########展示商品页面简单购物车##################
class CartsSimpleView(View):
    """商品页面右上角购物车"""

    def get(self, request):
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，查询Redis购物车
            redis_con = get_redis_connection('carts')
            redis_cart = redis_con.hgetall('carts_%s' % user.id)
            redis_selected = redis_con.smembers('selected_%s' % user.id)
            # 将redis中的两个数据统一格式，跟cookie中的格式一致，方便统一查询
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        else:
            # 用户未登录，查询cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        # 构造简单购物车JSON数据
        cart_list = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_list})



######################编码################################

# import pickle
# import base64
# # 组织数据
# carts={
#     '1':{'count':5,'selected':True}
# }
# # 5.1 将字典转换为二进制
# bytes_data=pickle.dumps(carts)
#
# # 5.2 再进行base64编码
# encode_data=base64.b64encode(bytes_data)
# encode_data
#
# #####################以下代码为解码#####################################
# # 5.3 先将base64解码
# decode_data=base64.b64decode(encode_data)
# # 5.4 将bytes类型转换为字典
# pickle.loads(decode_data)

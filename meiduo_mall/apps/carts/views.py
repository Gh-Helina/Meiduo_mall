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
from django.http import JsonResponse
# Create your views here.
from django.views import View
from django_redis import get_redis_connection

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
    def post(self,request):

        # 1.接收数据,判断商品信息
        json_data=json.loads(request.body.decode())
        sku_id=json_data.get('sku_id')
        count=json_data.get('count')
        if not all([sku_id,count]):
            return JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'参数不全'})
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'没有此商品'})

        try:
            count=int(count)
        except Exception:
            return JsonResponse({'code':RETCODE.PARAMERR,'errmsg':"参数错误"})
        #添加购物车默认就是选中
        selected=True
        # 2.先获取用户信息
        user=request.user
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
            redis_conn.hset('carts_%s'%user.id,sku_id,count)
            # set
            redis_conn.sadd('selected_%s'%user.id,sku_id)
            #     4.3 返回相应
            return JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

        else:
            # 5.未登录用户操作cookie

            # 5.0 先获取cookie中 可能存在的数据
            carts_str=request.COOKIES.get('carts')
            if carts_str is None:
                #说明没有购物车数据
                cookie_data = {
                    sku_id: {'count': count, 'selected': True}
                }
            else:
                #说明有购物车数据
                # 先base64解码
                decode_data=base64.b64decode(carts_str)
                # 再bytes转字典
                cookie_data=pickle.loads(decode_data)
                # 再需要进行判断
                # {1:{count:5,selected:True}}
                # 商品id是否在字典中
                # 1
                if sku_id in cookie_data:

                    #累加数量
                    origin_count=cookie_data[sku_id]['count']
                    # count=origin_count+count
                    count+=origin_count
                    #更新字典数据
                    cookie_data[sku_id]={'count':count,'selected':True}
                else:
                    cookie_data[sku_id]={'count':count,'selected':True}

            #     5.1 组织数据
            """
            {
                sku_id:{count:5,selected:True},
                sku_id:{count:2,selected:False},
                sku_id:{count:7,selected:True},
            }
            """

            #     5.2 对数据进行编码
            #  字典转bytes
            cookie_bytes=pickle.dumps(cookie_data)
            #  base64编码
            cookie_str=base64.b64encode(cookie_bytes)
            #     5.3 设置cookie
            response=JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})

            response.set_cookie('carts',cookie_str,max_age=7*24*3600)

            #     5.4 返回相应
            return response





















######################以下代码为编码################################

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


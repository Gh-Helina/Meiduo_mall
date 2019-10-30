from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.goods.models import SKU, GoodsCategory, GoodsVisitCount
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE


# 排序加分页
class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page):
        """提供商品列表页"""

        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return render(request, '404.html')
        # 1.根据分类，查询所有数据
        data = SKU.objects.filter(category=category)
        # 面包屑导航  将它抽取出去
        breadcrumb = get_breadcrumb(category)

        # 2.添加排序
        # default:上架时间
        # hot:热销
        # price:价格
        sort = request.GET.get('sort')
        if sort == 'defalt':
            order_filed = 'create_time'
        elif sort == 'hot':
            order_filed = 'sales'
        else:
            order_filed = '-price'
        data = SKU.objects.filter(category=category).order_by(order_filed)
        # 3.添加分页
        from django.core.paginator import Paginator
        # 3.1创建分页对象
        paginator = Paginator(object_list=data, per_page=5)
        # 3.2 获取指定页面数据
        page_data = paginator.page(page)
        total_page = paginator.num_pages
        # 3.3获取总页数
        context = {

            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_data,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page,  # 当前页码
        }
        return render(request, 'list.html', context=context)


#################热销数据###################
class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""
        # ​    1）获取分类id
        # ​    2）判断分类id是否正确
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '无数据'})
        # 根据销量倒序
        # 3）根据分类id进行查询[SKU。。]
        skus = SKU.objects.filter(category=category).order_by('-sales')[:2]
        hotskus = []
        # 4）将对象列表转换为字典
        #
        # ​    5）返回响应
        for sku in skus:
            hotskus.append({

                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price

            })
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'hot_skus': hotskus})


###########详情页##############
from django import http
from django.shortcuts import render
from django.views import View
from apps.contents.utils import get_categories
from apps.goods.models import SKU, GoodsCategory
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE


# 详情页
class DetailView(View):
    def get(self, request, sku_id):

        # 获取当前sku的信息
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,
        }

        return render(request, 'detail.html', context)


# class VisitCountView(View):
#     def post(self, request,category_id):
#         # 1.获取分类id
#         try:
#             category = GoodsCategory.objects.get(id=category_id)
#         except GoodsCategory.DoesNotExist:
#             return JsonResponse({'code':RETCODE.NODATAERR,'errmsg':' 没有此分类'})
#
#             # 2.获取今天日期
#         from django.utils import timezone
#         tody = timezone.localdate()
#             # 3.增加访问量
#             # 3.1
#             # 根据分类id和日期查询数据库是否已经有今天的指定的分类记录，有加1，没有创建
#         try:
#             vc = GoodsVisitCount.object.get(category=category, date=tody)
#         except GoodsVisitCount.DoesNotExist:
#             # 不存在
#             GoodsVisitCount.objects.create(
#                 category=category,
#                 date=tody,
#                 count=1
#             )
#             return JsonResponse({'code':RETCODE.OK,'errmsg':'ok'})
#         else:
#             # 存在
#             vc.count+=1
#             vc.save()
#
#             return JsonResponse({'code ': RETCODE.OK, 'errmsg': 'ok'})

"""
1.功能分析
    用户行为:    用户点击了某一个商品/某一个类别,应该+1
    前端行为:       前端必须给我分类id
    后端行为:    统计每一个商品分类在每一天中的访问量

2. 分析后端实现的大体步骤
        1.分类id
        2.获取今天的日期
        3.增加访问量

3.确定请求方式和路由
    GET
    POST  detail/visit/cat_id/
"""


# 商品分类统计
class VisitCountView(View):
    def post(self, request, category_id):
        # 1.分类id
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有此分类'})
        # 2.获取今天的日期

        from django.utils import timezone
        today = timezone.localdate()
        # 3.增加访问量
        # 3.1 我们要根据 分类id和日期,查询数据库 是否已经有今天的指定的分类记录
        try:
            vc = GoodsVisitCount.objects.get(category=category, date=today)
        except GoodsVisitCount.DoesNotExist:
            # 不存在
            # 添加记录 count=1
            GoodsVisitCount.objects.create(
                category=category,
                date=today,
                count=1
            )

            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        else:
            # 存在,存在就将count+1
            vc.count += 1
            vc.save()
            return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


# 展示订单
class InfoView(View):
    def get(self, request, page_num):
        # 查询当前登录用户的所有订单
        order_list = request.user.orders.order_by('-create_time')
        # 分页
        # 3.添加分页
        from django.core.paginator import Paginator
        # 3.1创建分页对象
        paginator = Paginator(object_list=order_list, per_page=1)
        # 获取当前页数据
        page_data = paginator.page(page_num)
        # 遍历当前页数据，转换页面中需要的结构
        order_list = []
        for order in page_data:
            # 获取当前订单中所有订单商品
            detail_list = []
            for detail in order.skus.all():
                detail_list.append({
                    'default_image_url': detail.sku.default_image.url,
                    'name': detail.sku.name,
                    'price': detail.price,
                    'count': detail.count,
                    'total_amount': detail.price * detail.count
                })
            order_list.append({
                'create_time': order.create_time,
                'order_id': order.order_id,
                'details': detail_list,
                'total_amount': order.total_amount,
                'freight': order.freight,
                'status': order.status
            })
        context = {
            'page': order_list,
            'page_num': page_num,  # 当期页码
            'total_page': paginator.num_pages  # 总页数
        }
        return render(request, 'user_center_order.html', context=context)

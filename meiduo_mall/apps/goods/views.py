from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.goods.models import SKU, GoodsCategory
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id,page):
        """提供商品列表页"""


        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return render(request, '404.html')
        # 1.根据分类，查询所有数据
        data=SKU.objects.filter(category=category)
        # 面包屑导航  将它抽取出去
        breadcrumb=get_breadcrumb(category)


        # 2.添加排序
        # default:上架时间
        # hot:热销
        # price:价格
        sort=request.GET.get('sort')
        if sort=='defalt':
            order_filed='create_time'
        elif sort=='hot':
            order_filed='sales'
        else:
            order_filed='-price'
        data=SKU.objects.filter(category=category).order_by(order_filed)
        # 3.添加分页
        from django.core.paginator import Paginator
        # 3.1创建分页对象
        paginator=Paginator(object_list=data,per_page=5)
        # 3.2 获取指定页面数据
        page_data=paginator.page(page)
        total_page=paginator.num_pages
        # 3.3获取总页数
        context={

            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_data,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page,  # 当前页码
        }
        return render(request, 'list.html',context=context)


#################热销数据###################
class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行JSON数据"""
        # ​    1）获取分类id
        # ​    2）判断分类id是否正确
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':RETCODE.NODATAERR,'errmsg':'无数据'})
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
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok','hot_skus':hotskus})

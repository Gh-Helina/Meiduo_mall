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


###########详情页##############
from django import http
from django.shortcuts import render
from django.views import View
from apps.contents.utils import get_categories
from apps.goods.models import SKU, GoodsCategory
from apps.goods.utils import get_breadcrumb
from utils.response_code import RETCODE


class DetailView(View):

    def get(self,request,sku_id):

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

        return render(request,'detail.html',context)

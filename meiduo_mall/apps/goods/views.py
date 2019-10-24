from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.goods.models import SKU, GoodsCategory


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id):
        """提供商品列表页"""

        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return render(request, '404.html')
        # 1.根据分类，查询所有数据
        data=SKU.objects.filter(category=category)

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

        return render(request, 'list.html')
        # return
from django.conf.urls import url
from . import views

urlpatterns = [
    # 排序加分页
    url(r'^list/(?P<category_id>\d+)/(?P<page>\d+)/$', views.ListView.as_view(), name='list'),
    # 热销页
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view(), name='hot'),
    # 详情页
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view(), name='detail'),
    # 商品分类统计
    url(r'^detail/visit/(?P<category_id>\d+)/$', views.VisitCountView.as_view(), name='detail/visit'),
    # 展示订单
    url('^orders/info/(?P<page_num>\d+)/$', views.InfoView.as_view(),name='order_info'),
]

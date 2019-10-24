from django.conf.urls import url
from . import views
urlpatterns = [
    #排序加分页
    url(r'^list/(?P<category_id>\d+)/(?P<page>\d+)/$',views.ListView.as_view(),name='list'),
    #热销页
    url(r'^hot/(?P<category_id>\d+)/$',views.HotGoodsView.as_view(),name='hot'),
]
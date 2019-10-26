from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^carts/$',views.CartsView.as_view(),name='carts'),
    url(r'^carts/selection/$',views.CartsSelectAllView.as_view(),name='carts/selection'),
]
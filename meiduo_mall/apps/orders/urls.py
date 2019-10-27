from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^placeorder/',views.PlaceOrderView.as_view(),name='placeorder'),
]
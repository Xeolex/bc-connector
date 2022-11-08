from django.urls import include, path
from adk_item_consumer.views import DeviceViewSet
from customer_portal_hawks.views import CustomerViewSet
from point_of_sales.views import PosViewSet
from rest_framework.routers import DefaultRouter,SimpleRouter


router = SimpleRouter()
router.register(r'device', DeviceViewSet, basename='device')
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'pos', PosViewSet, basename='pos')


# app_name = 'adk_item_consumer'

urlpatterns = router.urls

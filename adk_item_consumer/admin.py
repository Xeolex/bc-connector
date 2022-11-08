from django.contrib import admin

from adk_item_consumer.models import *

# Register your models here.







class TenantItem_admin(admin.ModelAdmin):
	list_display = [field.name for field in TenantItem._meta.fields if field.name != "id"]
admin.site.register(TenantItem,TenantItem_admin)

class TenantTransection_admin(admin.ModelAdmin):
	list_display = [field.name for field in TenantTransection._meta.fields if field.name != "id"]
admin.site.register(TenantTransection,TenantTransection_admin)

class TenantTransectionDetail_admin(admin.ModelAdmin):
	list_display = [field.name for field in TenantTransectionDetail._meta.fields if field.name != "id"]
admin.site.register(TenantTransectionDetail,TenantTransectionDetail_admin)
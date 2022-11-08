from django.contrib import admin
from bc_connect.models import *

# Register your models here.


class Tenant_admin(admin.ModelAdmin):
	list_display = [field.name for field in Tenant._meta.fields if field.name != "id"]
admin.site.register(Tenant,Tenant_admin)


class TenantApi_admin(admin.ModelAdmin):
	list_display = [field.name for field in TenantApi._meta.fields if field.name != "id"]
admin.site.register(TenantApi,TenantApi_admin)

class TenantUser_admin(admin.ModelAdmin):
	list_display = [field.name for field in TenantUser._meta.fields if field.name != "id"]
admin.site.register(TenantUser,TenantUser_admin)



class ApiRequest_admin(admin.ModelAdmin):
	# list_display = [field.name for field in ApiRequest._meta.fields if field.name != "id"]
	list_display = ['url','method','param','body', 'response_short','created','updated']
	def response_short(self, obj):
		if obj.response:
			return obj.response[:250]
		else:
			return obj.response

admin.site.register(ApiRequest,ApiRequest_admin)

class ApiTraffic_admin(admin.ModelAdmin):
	# list_display = [field.name for field in ApiTraffic._meta.fields if field.name != "id"]
	list_display = ['ApiRequest','api','view','method', 'param','body' ,'response_short','created','updated']
	def response_short(self, obj):
		if obj.response:
			return obj.response[:250]
		else:
			return obj.response
admin.site.register(ApiTraffic,ApiTraffic_admin)

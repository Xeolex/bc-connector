from django.db import models
from django.contrib.auth.models import User
# from adk_item_consumer.models import *




class Tenant(models.Model):
    AType = (('POS', 'POS'),('Customer Portal', 'Customer Portal'),('Item Consuption', 'Item Consuption'),)
    authtype = (('Oauth', 'Oauth'),('Key', 'Key'))
    name = models.CharField(max_length=250)
    tenant_id = models.CharField(max_length=250,blank=True,null=True)
    company_id = models.CharField(max_length=250)
    tenant_user = models.CharField(max_length=250)
    key = models.CharField(max_length=250,blank=True,null=True)
    scope = models.CharField(max_length=250,blank=True,null=True)
    token = models.CharField(max_length=2000,blank=True,null=True)
    localkey = models.CharField(max_length=250,blank=True,null=True)
    app_type = models.CharField(choices=AType,max_length=250)
    auth_type = models.CharField(choices=authtype,max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.name)

class TenantUser(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,null=True,blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True,blank=True)
    username = models.CharField(max_length=250,null=True,blank=True)
    password = models.CharField(max_length=250,null=True,blank=True)
    full_name = models.CharField(max_length=250,null=True,blank=True)
    licenseType = models.CharField(max_length=250,null=True,blank=True)
    authenticationEmail = models.CharField(max_length=250,null=True,blank=True)
    state = models.CharField(max_length=250,null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.tenant) + ' ' +str(self.username)


class TenantApi(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=250)
    baseurl = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.name)


class ApiRequest(models.Model):
    url = models.CharField(max_length=500,null=True,blank=True)
    method = models.CharField(max_length=25,null=True,blank=True)
    param = models.CharField(max_length=250,null=True,blank=True)
    body = models.CharField(max_length=250,null=True,blank=True)
    response = models.TextField(null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated = models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self):
        return str(self.url)

class ApiTraffic(models.Model):
    ApiRequest = models.ForeignKey(ApiRequest, on_delete=models.CASCADE,null=True,blank=True)
    api = models.CharField(max_length=500,null=True,blank=True)
    view = models.CharField(max_length=50,null=True,blank=True)
    method = models.CharField(max_length=25,null=True,blank=True)
    param = models.CharField(max_length=250,null=True,blank=True)
    body = models.CharField(max_length=250,null=True,blank=True)
    response = models.TextField(null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated = models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self):
        return str(self.api)        
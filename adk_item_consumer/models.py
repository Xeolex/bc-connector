from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from bc_connect.models import *





class TenantItem(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,null=True,blank=True)
    item_no = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    reference_no = models.CharField(max_length=250)
    system_modified_at = models.DateTimeField()
    stationConsumption = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.item_no)

class TenantTransection(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE,null=True,blank=True)
    journal_template_name = models.CharField(max_length=250)
    journal_batch_name = models.CharField(max_length=250)
    bin_code = models.CharField(max_length=250)
    employee_id = models.CharField(max_length=250)
    registering_date = models.DateField()
    response = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.journal_template_name)

class TenantTransectionDetail(models.Model):
    transection = models.ForeignKey(TenantTransection, on_delete=models.CASCADE,null=True,blank=True)
    expiration_date = models.CharField(max_length=250)
    location_code = models.CharField(max_length=250)
    item_no = models.CharField(max_length=250)
    lot_no = models.CharField(max_length=250)
    serial_no = models.CharField(max_length=250)
    patient_no = models.CharField(max_length=250)
    quantity = models.CharField(max_length=250)
    response = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.item_no)


from django_cron import CronJobBase, Schedule
import requests,pickle,os,json
from bc_connect.models import *
from adk_item_consumer.models import *
from django.utils import timezone
from django_cron.models import CronJobLog
from django.db.models import Q
from django.conf import settings
from requests.auth import HTTPBasicAuth


class ItemSync(CronJobBase):
    RUN_EVERY_MINS = 120 # every 2 hours


    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'adk_item_consumer.ItemSync'    # a unique code

    def do(self):
        x = CronJobLog.objects.filter(start_time__lt = timezone.now().date()).delete()
        tenant = Tenant.objects.filter(localkey = '38ced4f2738611255709d6e03bc3d2da111').first()
        tenantapi = TenantApi.objects.filter(tenant =tenant,name = 'adkurl').first()
        auth=HTTPBasicAuth(tenant.tenant_user, tenant.key)
        # auth=HTTPBasicAuth('D04', 'Adk@2021')
        url  = tenantapi.baseurl.replace('{company_id}',tenant.company_id) +'/itemsExpanded'
        if tenant.tenant_id == "None":
            param = {}
        else:
            param = {"Tenant":tenant.tenant_id}
        response = requests.get(url,  auth=auth,params=param)
        data = response.json()
        print(data)
        for dat in data['value']:
            print(dat)
            item = TenantItem.objects.filter(tenant = tenant, item_no = dat['itemNo'], description = dat['description'] , reference_no = dat['reference_No_']).first()
            if item:
                item.stationConsumption =  dat['stationConsumption']
                item.system_modified_at  = dat['systemModifiedAt']
                item.save()
            else:
                item  = TenantItem()
                item.tenant = tenant
                item.stationConsumption = dat['stationConsumption']
                item.item_no = dat['itemNo']
                item.description = dat['description']
                item.reference_no = dat['reference_No_']
                item.system_modified_at  = dat['systemModifiedAt']
                item.save()







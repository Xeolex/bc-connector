from django.shortcuts import render
from rest_framework.decorators import api_view,authentication_classes,permission_classes,action,parser_classes
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED
)
from rest_framework.response import Response
from adk_item_consumer.models import *
from adk_item_consumer.func import *
from rest_framework import viewsets
import requests
from requests.auth import HTTPBasicAuth
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
import json,os
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from datetime import date,datetime
import csv
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
import base64
from django.http import FileResponse
from django.utils.encoding import smart_str
from django.db.models import Q
import hashlib
import time
from bc_connect.func import *


# Create your views here.
@api_view(["GET"])
def index(request):
	contant = {'data':'data'}

	return Response(contant,status=HTTP_200_OK) 



class DeviceViewSet(viewsets.ViewSet):
	@action(detail=False, methods=['post'], permission_classes=[AllowAny],authentication_classes=[])
	def login(self, request):
		print('----------login---------')
		api_request = ApiRequest()
		api_request.url ='/devices/login/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()
		
		local_key = request.data.get('local_key')
		username = request.data.get('username')
		password = request.data.get('password')
		if not local_key or not username or not password:
			contant ={'detail':'Required infomation not provided'}
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		
		tenant = Tenant.objects.filter(localkey = local_key).first()
		if not tenant:
			contant ={'detail':'Tenant not found'}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)

		if tenant.tenant_id == 'None':
			param = {"$filter":"userID eq '"+username+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"userID eq '"+username+"'"}

		header = {}
		data = call_BC(rq = api_request, api_type='adkurl',api='icaUsers',tenant=tenant,param=param,method ='get',view='login',header=header)

		if 'error' in data:
			contant ={'detail':data['error']['code']}
			return Response(contant,status=HTTP_404_NOT_FOUND)
		if 'value' not in data:
			contant ={'detail':'User not found'}
			return Response(contant,status=HTTP_404_NOT_FOUND)
		if len(data['value']) == 0 :
			contant ={'detail':'User not found'}
			return Response(contant,status=HTTP_404_NOT_FOUND)

		
		user = data['value'][0]
		userobj = User.objects.filter(username = user['id']).first()
		if userobj:
			tenantuser = TenantUser.objects.filter(user = userobj).first()
			if tenantuser:
				tenantuser.username = user['userID']
				tenantuser.password = password
				tenantuser.full_name = user['fullName']
				tenantuser.save()
			else:
				tenantuser = TenantUser()
				tenantuser.user = userobj
				tenantuser.tenant = tenant
				tenantuser.username = user['userID']
				tenantuser.password = password
				tenantuser.full_name = user['fullName']
				tenantuser.save()
			login_user = authenticate(username=userobj.username, password='backslash@portal.bc')
			token  = Token.objects.filter(user=login_user).delete()
			token, _ = Token.objects.get_or_create(user=login_user)
		else:
			userobj = User.objects.create_user(username = user['id'], password =  'backslash@portal.bc')
			userobj.save()
			tenantuser = TenantUser()
			tenantuser.user = userobj
			tenantuser.tenant = tenant
			tenantuser.username = user['userID']
			tenantuser.password = password
			tenantuser.full_name = user['fullName']
			tenantuser.save()
			login_user = authenticate(username=userobj.username, password='backslash@portal.bc')
			token  = Token.objects.filter(user=login_user).delete()
			token, _ = Token.objects.get_or_create(user=login_user)

		contant = {
			'details':'OK',
			'data':{
				'token':token.key,
				'username':tenantuser.username,
				'full_name':tenantuser.full_name
				}
			}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'])
	def get_staff(self, request):
		print('----------get_staff---------')
		api_request = ApiRequest()
		api_request.url ='/devices/get_staff/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		staff_id = request.GET.get('staff_id')
		if staff_id == None:
			contant ={'detail':'Staff ID not provided'}
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		login_user = request.user
		tenantuser = login_user.tenantuser
		tenant = login_user.tenantuser.tenant
		
		if tenant.tenant_id == 'None':
			param = {"$filter":"number eq '"+staff_id+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"number eq '"+staff_id+"'"}
		header = {}
		data = call_BC(rq = api_request, api_type='bcv2',api='employees',tenant=tenant,param=param,method ='get',view='get_staff',header=header)
		
		if len(data['value']) == 0:
			staff_id = staff_id.rjust(6, '0')

			if tenant.tenant_id == 'None':
				param = {"$filter":"number eq '"+staff_id+"'"}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"number eq '"+staff_id+"'"}

			data = call_BC(rq = api_request, api_type='bcv2',api='employees',tenant=tenant,param=param,method ='get',view='get_staff',header=header)

			if len(data['value']) == 0:
				contant ={'detail':'Staff not found'}
				return Response(contant,status=HTTP_404_NOT_FOUND)

		staff = data['value'][0]

		contant = {
			'details':'OK',
			'data':{
				'staff':{
					'id':staff['number'],
					'name':staff['displayName'],
					'job_title':staff['jobTitle'],
					}
				}
			}
		
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'])
	def get_patient(self, request):
		print('----------get_patient---------')
		api_request = ApiRequest()
		api_request.url ='/devices/get_patient/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()


		patient_id = request.GET.get('patient_id')
		if patient_id == None:
			contant ={'detail':'Patient ID not provided'}
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		login_user = request.user
		tenantuser = login_user.tenantuser
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$filter":"no eq '"+patient_id+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"no eq '"+patient_id+"'"}
		header = {}
		data = call_BC(rq = api_request, api_type='adkurl',api='patients',tenant=tenant,param=param,method ='get',view='get_staff',header=header)


		if 'value' in data:
			if len(data['value']) == 0:
				if patient_id == tenantuser.username:
					contant = {
						'details':'OK',
						'data':{
							'patient':{
								'id': patient_id,
								'name':patient_id,
								'identification':patient_id,
								'type':'Station'
								}
							}
						}
					return Response(contant,status=HTTP_200_OK)
				else:
					contant ={'detail':'Patient or Station not found'}
					return Response(contant,status=HTTP_404_NOT_FOUND)
		else:
			contant ={'detail':'Patient or Station not found'}
			return Response(contant,status=HTTP_404_NOT_FOUND)
			
		patient = data['value'][0]
		contant = {
			'details':'OK',
			'data':{
				'patient':{
					'id':patient['no'],
					'name':patient['name'],
					'identification':patient['identification'],
					'type':'Patient'
					}
				}
			}
		
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)


	@action(detail=False, methods=['get'])
	def search_item(self, request):
		print('----------search_item---------')
		api_request = ApiRequest()
		api_request.url ='/devices/search_item/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		keyword = request.GET.get('keyword')
		login_user = request.user
		tenantuser = login_user.tenantuser
		tenant = login_user.tenantuser.tenant

		if keyword == None:
			itemsq = TenantItem.objects.filter(tenant = tenantuser.tenant)
		else:
			itemsq = TenantItem.objects.filter(Q(tenant = tenantuser.tenant,item_no=keyword) | Q(tenant = tenantuser.tenant,reference_no = keyword) | Q(tenant = tenantuser.tenant,description__icontains = keyword.lower()))
		

		item_ar = []
		items_obj = []
		
		if tenant.tenant_id == 'None':
			param = {"$filter":"binCode eq '"+tenantuser.username+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"binCode eq '"+tenantuser.username+"'"}
		header = {}
		data = call_BC(rq = api_request, api_type='adkurl',api='binContents',tenant=tenant,param=param,method ='get',view='get_staff',header=header)

		for itemq in itemsq:
			aa  = [itemq.item_no,itemq.description]
			if aa not in item_ar:
				if 'value' in data:
					for dat in data['value']:
						if dat['itemNo'] == itemq.item_no:
							qtya = int(dat['quantity']) - int(dat['negAdjmtQty'])
							if int(qtya) > 0:
								item_obj = {
									'id':hash(str(itemq.item_no)+str(dat['lotNo'])+str(dat['serialNo'])),
									'number':itemq.item_no,
									'name': itemq.description,
									'expiry': dat['expirationDate'],
									'stock': qtya,
									'lot_no': dat['lotNo'],
									'serial_no': dat['serialNo'],
									'stationConsumption': itemq.stationConsumption,
									'unitofMeasureCode': dat['unitofMeasureCode'],
									'item_search': itemq.item_no + '!' + dat['lotNo'] +'!' +dat['unitofMeasureCode'],
								}
								items_obj.append(item_obj)

				item_ar.append(aa)
		

		contant = {
			'details':'OK',
			'data':{
				'items':items_obj
				}
			}
		
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)


	@action(detail=False, methods=['post'])
	def item_journal(self, request):
		print('----------item_journal---------')
		api_request = ApiRequest()
		api_request.url ='/devices/item_journal/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		staff = request.data.get('staff')
		patient = request.data.get('patient')
		items = request.data.get('items')
		
		if staff == None or items == None or patient == None:
			contant ={'detail':'Required infomation not provided'}
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		elif len(items) == 0:
			contant ={'detail':'Required infomation not provided'}
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		login_user = request.user
		tenantuser = login_user.tenantuser
		tenant = login_user.tenantuser.tenant

		for item in items:			
			if tenant.tenant_id == 'None':
				param = {"$filter":"binCode eq '"+tenantuser.username+"' and itemNo eq '"+ item['number']+ "' and lotNo eq '"+ item['lot_no'] +"' and serialNo eq '"+item['serial_no'] +"' and expirationDate eq "+item['expiry']}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"binCode eq '"+tenantuser.username+"' and itemNo eq '"+ item['number']+ "' and lotNo eq '"+ item['lot_no'] +"' and serialNo eq '"+item['serial_no'] +"' and expirationDate eq "+item['expiry']}
			header = {}
			data = call_BC(rq = api_request, api_type='adkurl',api='binContents',tenant=tenant,param=param,method ='get',view='item_journal',header=header)


			if 'value' in data:
				for dat in data['value']:
					qtya = int(dat['quantity']) - int(dat['negAdjmtQty'])
					if (qtya) < item['qty']:
						contant ={'detail':'Stock not available for '+item['number'] +' lot_no '+item['lot_no']}
						return Response(contant,status=HTTP_400_BAD_REQUEST)
		line_no = 101

		tr = TenantTransection()
		tr.tenant = tenantuser.tenant
		tr.journal_template_name = 'ADJMT'
		tr.journal_batch_name = tenantuser.username
		tr.bin_code = tenantuser.username
		tr.employee_id = staff
		tr.registering_date = datetime.today().strftime('%Y-%m-%d')
		tr1 = tr.save()

		print('-----------add items----------------')
		for item in items:
			if abs(item['qty']) != 0:
				if item['stationConsumption'] == True:
					j_patient = tenantuser.username
				else:
					j_patient = patient
				line_no += 1
				post_data = {
						    'journal_template_name': 'ADJMT',
						    'journal_batch_name': tenantuser.username,
						    'expiration_date':item['expiry'],
						    'location_code': "10",
						    'item_no': item['number'],
						    'quantity': abs(item['qty'])*-1,
						    'bin_code': tenantuser.username,
						    'patient_no': j_patient,
						    'registering_date':datetime.today().strftime('%Y-%m-%d'),
						    'employee_id':staff,
						    'lot_no':item['lot_no'],
						    'serial_no':item['serial_no']
							}
				print(post_data)
				header = {"Content-Type":"application/json"}
				if tenant.tenant_id == 'None':
					param = {}
				else:
					param = {"Tenant":tenant.tenant_id}
				data = call_BC(rq = api_request,api_type='adkurl',api='WarehouseItemJournals', tenant=tenant,param=param,method ='post',view='item_journal',header=header,body=json.dumps(post_data))
				print('jskdhfkdshfkjhdsfds',data)
				# time.sleep(10)
				if 'error' not in data:
					tr_d = TenantTransectionDetail()
					tr_d.transection = tr
					tr_d.expiration_date = data['expiration_date']
					tr_d.location_code = data['location_code']
					tr_d.item_no = data['item_no']
					tr_d.lot_no = data['lot_no']
					tr_d.serial_no = data['serial_no']
					tr_d.patient_no = data['patient_no']
					tr_d.quantity = data['quantity']
					tr_d.save()

					print('-----------register items----------------')
					header = {"Content-Type":"application/json"}
					if tenant.tenant_id == 'None':
						param = {"$filter":"journal_batch_name eq '"+data['journal_batch_name']+"' and journal_template_name eq '"+data['journal_template_name']+"'"}
					else:
						param = {"Tenant":tenant.tenant_id,"$filter":"journal_batch_name eq '"+data['journal_batch_name']+"' and journal_template_name eq '"+data['journal_template_name']+"'"}
					
					data = call_BC(rq = api_request, api_type='adkurl',api='WarehouseItemJournalsRegister',tenant=tenant,param=param,method ='get',view='get_staff',header=header)

					tr_d.response = str(data)
					tr_d.save()

				elif 'error' in data:
					tr_d = TenantTransectionDetail()
					tr_d.transection = tr
					tr_d.expiration_date = item['expiry']
					tr_d.location_code = '10'
					tr_d.item_no = item['number']
					tr_d.lot_no = item['lot_no']
					tr_d.serial_no = item['serial_no']
					tr_d.patient_no = j_patient
					tr_d.quantity = item['qty']*-1
					tr_d.response = str(data)
					tr_d.save()
					contant ={'detail': 'Contact Support. '+ data['error']['code']}
					return Response(contant,status=HTTP_400_BAD_REQUEST)
				else:
					contant ={'detail': 'Contact Support.'}
					return Response(contant,status=HTTP_400_BAD_REQUEST)

		contant = {
			'details':'Items posted',
			}
		
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)





	@action(detail=False, methods=['get'])
	def get_transections(self, request):
		print('----------get_transections---------')
		api_request = ApiRequest()
		api_request.url ='/devices/get_transections/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenantuser = login_user.tenantuser
		tenant = login_user.tenantuser.tenant

		tr_obj = []
		for tr in TenantTransection.objects.filter(bin_code = tenantuser.username).order_by('-id')[:100]:
			ar_itm =[]
			for it in TenantTransectionDetail.objects.filter(transection = tr):
				itm ={
					'item_no':it.item_no,
					'lot_no': it.lot_no,
					'patient_no': it.patient_no,
					'expiration_date': it.expiration_date,
					'quantity': it.quantity

				}
				ar_itm.append(itm)
			item_obj = {
						'id':tr.id,
						'bin_code':tr.bin_code,
						'employee_id': tr.employee_id,
						'registering_date': tr.registering_date,
						'items':ar_itm
					}
			tr_obj.append(item_obj)

		

		contant = {
			'details':'OK',
			'data':{
				'transections':tr_obj
				}
			}
		
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)



    

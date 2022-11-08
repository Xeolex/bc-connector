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
from bc_connect.models import *
from bc_connect.models import *
from bc_connect.func import *
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
import hashlib
from wsgiref.util import FileWrapper


# Create your views here.
@api_view(["GET"])
def index(request):
	contant = {'data':'data'}
	#print(contant)
	return Response(contant,status=HTTP_200_OK) 



class CustomerViewSet(viewsets.ViewSet):

	@action(detail=False, methods=['post'], permission_classes=[AllowAny],authentication_classes=[])
	def login(self, request):
		rate = 1
		print('----------login---------')
		api_request = ApiRequest()
		api_request.url ='/customers/login/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()


		local_key = request.data.get('local_key')
		email = request.data.get('email')
		password = request.data.get('password')
		password_hash = str(hashlib.md5(password.encode('utf-8')).hexdigest()).upper()
		print(local_key)
		header = {"Content-Type":"application/json"}
		if not local_key or not email or not password:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Required infomation not provided'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_200_OK) 
		tenant = Tenant.objects.filter(localkey = local_key).first()
		if not tenant:
			contant ={'response':{'code':HTTP_404_NOT_FOUND,'msg':'Tenant not found'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)

		if tenant.tenant_id == 'None':
			param = {"$filter":"username eq '"+email+"'  and password eq '"+password_hash+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"username eq '"+email+"'  and password eq '"+password_hash+"'" }

		user1 = call_BC(rq = api_request, api_type='piurl',api='portalUsers',tenant=tenant,param=param,method ='get',view='login',header=header)


		if 'value' not in user1:
			contant = {'response':{'code':HTTP_404_NOT_FOUND,'msg':'Invalid login details'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)
		elif len(user1['value']) == 0:
			contant = {'response':{'code':HTTP_404_NOT_FOUND,'msg':'Invalid login details'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)

		user1 = user1['value'][0]

		if tenant.tenant_id == 'None':
			param = {"$filter":"customerNumber eq '"+user1['customerNo']+"' and date_filter eq '"+ str(date.today()) +"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"customerNumber eq '"+user1['customerNo']+"'  and date_filter eq '"+ str(date.today()) +"'"}
		
		data = call_BC(rq = api_request, api_type='piurl',api='customerPortalUsers',tenant=tenant,param=param,method ='get',view='login')
		
		if 'value' not in data:
			contant = {'response':{'code':HTTP_404_NOT_FOUND,'msg':'Invalid Customer'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)
		elif len(data['value']) == 0:
			contant = {'response':{'code':HTTP_404_NOT_FOUND,'msg':'Invalid Customer'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)


		user = data['value'][0]
		if user['cpStatus'] != "Approved":
			contant = {'response':{'code':HTTP_401_UNAUTHORIZED,'msg':'Account not approve. Contact '+ tenant.name +' to approve your account.'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)


		userobj = User.objects.filter(username = str(user1['id'])+str(user1['systemId'])  ) .first()

		if userobj:
			userobj.first_name = user1['customerNo']
			userobj.last_name = user['id']
			userobj.save()
			login_user = authenticate(username=userobj.username, password='backslash@portal.bc')
			# token  = Token.objects.filter(user=login_user).delete()
			token, _ = Token.objects.get_or_create(user=login_user)
		else:
			userobj = User.objects.create_user(str(user1['id'])+str(user1['systemId']), user1['username'], 'backslash@portal.bc',first_name = user1['customerNo'],last_name = user['id'])
			userobj.save()
			tenantuser = TenantUser()
			tenantuser.user = userobj
			tenantuser.tenant = tenant
			tenantuser.username = user1['username']
			tenantuser.save()
			login_user = authenticate(username=userobj.username, password='backslash@portal.bc')
			token, _ = Token.objects.get_or_create(user=login_user)




		


		if tenant.tenant_id == 'None':
			param = {"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and invoiceDate ge " +str(date.today().year-1)+'-01-01' }
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and invoiceDate ge " +str(date.today().year-1)+'-01-01' }

		data = call_BC(rq = api_request,api_type='bcv2',api='salesInvoices',tenant=tenant,param=param,method ='get',view='login')

		this_jan = 0
		this_feb = 0
		this_mar = 0
		this_apr = 0
		this_may = 0
		this_jun = 0
		this_jul = 0
		this_aug = 0
		this_sep = 0
		this_oct = 0
		this_nov = 0
		this_dec = 0
		last_jan = 0
		last_feb = 0
		last_mar = 0
		last_apr = 0
		last_may = 0
		last_jun = 0
		last_jul = 0
		last_aug = 0
		last_sep = 0
		last_oct = 0
		last_nov = 0
		last_dec = 0
		if 'value' in data:
			for inv in data['value']:
				inv_month = inv['invoiceDate'][:7]
				if  inv_month == str(date.today().year)+'-01':
					this_jan += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-02':
					this_feb += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-03':
					this_mar += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-04':
					this_apr += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-05':
					this_may += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-06':
					this_jun += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-07':
					this_jul += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-08':
					this_aug += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-09':
					this_sep += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-10':
					this_oct += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-11':
					this_nov += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-12':
					this_dec += round(float(inv['totalAmountIncludingTax']))
				
				if  inv_month == str(date.today().year-1)+'-01':
					last_jan += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-02':
					last_feb += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-03':
					last_mar += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-04':
					last_apr += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-05':
					last_may += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-06':
					last_jun += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-07':
					last_jul += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-08':
					last_aug += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-09':
					last_sep += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-10':
					last_oct += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-11':
					last_nov += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-12':
					last_dec += round(float(inv['totalAmountIncludingTax']))


		if tenant.tenant_id == 'None':
			param = {"$filter":"code eq 'C-PORTAL'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"code eq 'C-PORTAL'"}
		header = {"Content-Type":"application/json"}
		journal = call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals',tenant=tenant,param=param,method ='get',view='login',header=header)

		if 'value' in journal:
			if tenant.tenant_id == 'None':
				param = {"$filter":"customerNumber eq '"+login_user.first_name+"'"}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"customerNumber eq '"+login_user.first_name+"'"}
			data_payments = call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals('+journal['value'][0]['id']+')/customerPayments' ,tenant=tenant,param=param,method ='get',view='login',header=header)

			data_payments = data_payments['value']

			unapproved_payemnt = 0

			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			data_cust = call_BC(rq = api_request,api_type='bcv2',api='customers('+user['id']+')',tenant=tenant,param=param,method ='get',view='login',header=header)

			if data_cust['currencyCode'] == None or data_cust['currencyCode'] == "":
				cur = 'MVR'
			else:
				cur = data_cust['currencyCode']
			if cur == "MVR":
				rate = 1
			else:
				rate = 15.42
			for data_payment in data_payments:
				unapproved_payemnt += data_payment['amount']*rate
		else:
			cur = 'Mvr'
			unapproved_payemnt = 0

		if user['overdueAmount'] > 0:
			warning = True
		else:
			warning = False

		if user['CurrencyCode'] == None or user['CurrencyCode'] == "":
			cur_code = 'MVR'
		else:
			cur_code = user['CurrencyCode']

		if cur_code == 'USD' or cur_code =='Usd' or cur_code == 'usd':
			cur_rate = 15.42
		else:
			cur_rate = 1

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'token':token.key,
			'customer':	{
				'customerNumber':user['customerNumber'],
				'name':user['name'],
				'phoneNo':user['phoneNo'],
				'eMail':user1['username'],
				'customerType':user['customerType'],
				'identificationNo':user['identificationNo'],
				'creditLimitLCY':str(round(float(user['creditLimitLCY'])/cur_rate,2)),
				'available_limit':round((float(user['creditLimitLCY'])-float(user['balance']))/cur_rate,2),
				'balance':round(float(user['balance'])/cur_rate,2),
				'totalSalesExcludingTax':round(float(user['totalSalesExcludingTax'])/rate,2),
				# 'overdueAmount':over_due_amount/rate,
				'warning':warning,
				'unapproved_payemnt':round(unapproved_payemnt/cur_rate,2),
				'contact_name':user['contact_name'],
				'currancy':cur_code,
				'approvedLimit':user['approvedLimit'],
				'tempCreditLimit':user['tempCreditLimit'],
				'tempCreditLimitDate':user['tempCreditLimitDate']
				}
				,
			'invoice_graph':[
							{
								'name': 'This Year',
								'data': [this_jan, this_feb, this_mar, this_apr, this_may, this_jun, this_jul, this_aug, this_sep, this_oct, this_nov, this_dec],
							},
							{
								'name': 'Last Year',
								'data': [last_jan, last_feb, last_mar, last_apr, last_may, last_jun, last_jul, last_aug, last_sep, last_oct, last_nov, last_dec],
							},
						]

			}
		}
		#print(contant)
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)



	@action(detail=False, methods=['get'])
	def get_dashboard(self, request):
		rate = 1
		print('------get_dashboard-------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_dashboard/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant
		
		if tenant.tenant_id == 'None':
			param = {"$filter":"date_filter eq '"+ str(date.today()) +"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"date_filter eq '"+ str(date.today()) +"'"}
		header = {"Content-Type":"application/json"}
		user = call_BC(rq = api_request,api_type='piurl',api='customerPortalUsers('+login_user.last_name+')',tenant=tenant,param=param,method ='get',view='dashboard',header=header)
		
		over_due_amount = round(float(user['overdueAmount']),2)

		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		header = {"Content-Type":"application/json"}
		user = call_BC(rq = api_request,api_type='piurl',api='customerPortalUsers('+login_user.last_name+')',tenant=tenant,param=param,method ='get',view='dashboard',header=header)

		tenantapi = TenantApi.objects.filter(tenant =tenant,name = 'bcv2').first()
		url  = tenantapi.baseurl.replace('{company_id}',tenant.company_id) +'salesInvoices'
		if tenant.tenant_id == 'None':
			param = {"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and invoiceDate ge " +str(date.today().year-1)+'-01-01' }
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and invoiceDate ge " +str(date.today().year-1)+'-01-01' }
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='bcv2',api='salesInvoices',tenant=tenant,param=param,method ='get',view='dashboard',header=header)

		this_jan = 0
		this_feb = 0
		this_mar = 0
		this_apr = 0
		this_may = 0
		this_jun = 0
		this_jul = 0
		this_aug = 0
		this_sep = 0
		this_oct = 0
		this_nov = 0
		this_dec = 0
		last_jan = 0
		last_feb = 0
		last_mar = 0
		last_apr = 0
		last_may = 0
		last_jun = 0
		last_jul = 0
		last_aug = 0
		last_sep = 0
		last_oct = 0
		last_nov = 0
		last_dec = 0
		if 'value' in data:
			for inv in data['value']:
				inv_month = inv['invoiceDate'][:7]
				if  inv_month == str(date.today().year)+'-01':
					this_jan += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-02':
					this_feb += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-03':
					this_mar += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-04':
					this_apr += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-05':
					this_may += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-06':
					this_jun += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-07':
					this_jul += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-08':
					this_aug += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-09':
					this_sep += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-10':
					this_oct += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-11':
					this_nov += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year)+'-12':
					this_dec += round(float(inv['totalAmountIncludingTax']))
				
				if  inv_month == str(date.today().year-1)+'-01':
					last_jan += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-02':
					last_feb += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-03':
					last_mar += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-04':
					last_apr += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-05':
					last_may += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-06':
					last_jun += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-07':
					last_jul += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-08':
					last_aug += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-09':
					last_sep += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-10':
					last_oct += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-11':
					last_nov += round(float(inv['totalAmountIncludingTax']))
				if  inv_month == str(date.today().year-1)+'-12':
					last_dec += round(float(inv['totalAmountIncludingTax']))

		if tenant.tenant_id == 'None':
			param = {"$filter":"code eq 'C-PORTAL'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"code eq 'C-PORTAL'"}
		header = {"Content-Type":"application/json"}
		journal =  call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals',tenant=tenant,param=param,method ='get',view='dashboard',header=header)

		if 'value' in journal:
			url  = tenantapi.baseurl.replace('{company_id}',tenant.company_id) +'customerPaymentJournals('+journal['value'][0]['id']+')/customerPayments'
			# param = {"$filter":"customerNumber eq '"+login_user.first_name+"'"}
			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			data_payments = call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals('+journal['value'][0]['id']+')/customerPayments',tenant=tenant,param=param,method ='get',view='dashboard',header=header)
			data_payments = data_payments['value']
			
			unapproved_payemnt = 0
			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			header = {"Content-Type":"application/json"}
			data_cust = call_BC(rq = api_request,api_type='bcv2',api='customers('+login_user.last_name+')', tenant=tenant,param=param,method ='get',view='dashboard',header=header)
			if data_cust['currencyCode'] == None or data_cust['currencyCode'] == "":
				cur = 'MVR'
			else:
				cur = data_cust['currencyCode']
			if cur == "MVR":
				rate = 1
			else:
				rate = 15.42
			for data_payment in data_payments:
				unapproved_payemnt += data_payment['amount']*rate
		else:
			cur = 'Mvr'
			unapproved_payemnt = 0
		if over_due_amount > 0:
			warning = True
		else:
			warning = False

		if user['CurrencyCode'] == None or user['CurrencyCode'] == "":
			cur_code = 'MVR'
		else:
			cur_code = user['CurrencyCode']

		if cur_code == 'USD' or cur_code =='Usd' or cur_code == 'usd':
			cur_rate = 15.42
		else:
			cur_rate = 1


		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer':	{
				'customerNumber':user['customerNumber'],
				'name':user['name'],
				'phoneNo':user['phoneNo'],
				'eMail':user['eMail'],
				'customerType':user['customerType'],
				'identificationNo':user['identificationNo'],
				'creditLimitLCY':str(round(float(user['creditLimitLCY'])/cur_rate,2)),
				'available_limit':round((float(user['creditLimitLCY'])-float(user['balance']))/cur_rate,2),
				'balance':round(float(user['balance'])/cur_rate,2),
				'totalSalesExcludingTax':round(float(user['totalSalesExcludingTax'])/rate,2),
				'overdueAmount':round(over_due_amount/rate,2),
				'warning':warning,
				'unapproved_payemnt':round(unapproved_payemnt/cur_rate,2),
				'contact_name':user['contact_name'],
				'currancy':cur_code,
				'approvedLimit':user['approvedLimit'],
				'tempCreditLimit':user['tempCreditLimit'],
				'tempCreditLimitDate':user['tempCreditLimitDate'] 
				},
			'invoice_graph':[
							{
								'name': 'This Year',
								'data': [this_jan, this_feb, this_mar, this_apr, this_may, this_jun, this_jul, round(this_aug), this_sep, this_oct, this_nov, this_dec],
							},
							{
								'name': 'Last Year',
								'data': [last_jan, last_feb, last_mar, last_apr, last_may, last_jun, last_jul, last_aug, last_sep, last_oct, last_nov, last_dec],
							},
						]


			}
		}
		#print(contant)
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)




	@action(detail=False, methods=['get'])
	def get_transections(self, request):

		print('----------get_transections---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_transections/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		date_from = request.GET.get('date_from')
		date_to = request.GET.get('date_to')
		download = request.GET.get('download')
		if date_to and date_from:
			if tenant.tenant_id == 'None':
				param = {"$filter":"customerNo eq '"+login_user.first_name+"'","$orderby":'entryNo desc' }
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"customerNo eq '"+login_user.first_name+"'","$orderby":'entryNo desc' }

		if tenant.tenant_id == 'None':
			param = {"$filter":"customerNo eq '"+login_user.first_name+"' and documentDate ge "+str(date.today().year)+'-'+str(date.today().month)+'-01',"$orderby":'entryNo desc' }
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"customerNo eq '"+login_user.first_name+"' and documentDate ge "+str(date.today().year)+'-'+str(date.today().month)+'-01',"$orderby":'entryNo desc' }
		
		if date_to and date_from:
			if tenant.tenant_id == 'None':
				param = {"$filter":"customerNo eq '"+login_user.first_name+"' and documentDate ge "+ date_from+" and documentDate le "+ date_to,"$orderby":'entryNo desc'}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"customerNo eq '"+login_user.first_name+"' and documentDate ge "+ date_from+" and documentDate le "+ date_to,"$orderby":'entryNo desc'}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='piurl',api='customerLedgerEntries', tenant=tenant,param=param,method ='get',view='transections',header=header)
			
		invs_dic = []
		if 'value' in data:
			for dat in data['value']:
				if dat['currencyCode'] == None or dat['currencyCode'] == '':
					cur = 'MVR'
				else:
					cur = dat['currencyCode']
				if 'poNumber' in dat:
					po_number = dat['poNumber']
				else:
					po_number = ''


				inv_dic = {
					'entryNo': dat['entryNo'],
		            'postingDate': dat['postingDate'],
		            'documentDate': dat['documentDate'],
		            'documentType': dat['documentType'],
		            'documentNo': dat['documentNo'],
		            'externalDocumentNo': dat['externalDocumentNo'],
		            'po_number': po_number,
		            'amount': dat['amount'],
		            'amountLCY': dat['amountLCY'],
		            'cur': cur,
		            'remainingAmount': dat['remainingAmount'],
		            'customerNo': dat['customerNo'],
		            'description': dat['description'],
		            'dueDate': dat['dueDate']
				}
				invs_dic.append(inv_dic)
		download_csv = os.path.join(settings.MEDIA_ROOT,'donwload',login_user.first_name+'.csv')
		url_csv = os.path.join(settings.MEDIA_URL,'donwload',login_user.first_name+'.csv')
		with open(download_csv, 'w', newline='') as csvfile:
		    writer = csv.writer(csvfile)
		    writer.writerow(['Number',  'Type', 'Date', 'Document No','External Document No','Po Number','Amount','Currancy','Remaining','Description'])
		    if 'value' in data:
			    for dat in data['value']:
			    	writer.writerow([dat['entryNo'], dat['documentType'],dat['documentDate'], dat['documentNo'],dat['externalDocumentNo'],po_number,dat['amount'],cur,dat['remainingAmount'],dat['description']])
		full_url_csv = 'https://'+ get_current_site(request).domain+url_csv
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_invoives':invs_dic,
			'csv':full_url_csv
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)


	@action(detail=False, methods=['get'])
	def get_invoices(self, request):
		print('----------get_invoices---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_invoices/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and postingDate ge " +str(date.today().year-1)+'-01-01',"$expand":'salesInvoiceLines',"$orderby":'dueDate'}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"billToCustomerNumber eq '"+login_user.first_name+"' and postingDate ge " +str(date.today().year-1)+'-01-01',"$expand":'salesInvoiceLines',"$orderby":'dueDate'}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='bcv2',api='salesInvoices', tenant=tenant,param=param,method ='get',view='invoices',header=header)
		# data = call_BC_v2(rq = api_request, api_type='bcv2',api='salesInvoices',tenant=tenant,param=param,method ='get',view='invoices',response_type='json',header=header)
		invs_dic = []
		invs_dic_due = []
		invs_dic_open = []
		if 'value' in data:
			for dat in data['value']:
				if dat['currencyCode'] == None or dat['currencyCode'] == '':
					cur = 'MVR'
				else:
					cur = dat['currencyCode']

				due_date = datetime.strptime(dat['dueDate'], "%Y-%m-%d").date()
				if due_date <  date.today() and float(dat['remainingAmount']) > 0:
					status = "Due"
					due_days = abs((date.today() - due_date).days)
				else:
					status = "Open"
					due_days = None
				if dat['status'] == "Open":
					in_status = status
				else:
					in_status = dat['status']
				if status == "Due":
					inv_due = {
						'id':dat['id'],
						'number':dat['number'],
						'shipToName':dat['shipToName'],
						'postingDate':dat['postingDate'],
						'dueDate':dat['dueDate'],
						'due_days':due_days,
						'totalAmountExcludingTax': round(dat['totalAmountExcludingTax'],2),
						'totalTaxAmount': round(dat['totalTaxAmount'],2),
						'totalAmountIncludingTax': round(dat['totalAmountIncludingTax'],2),
						'remainingAmount': round(dat['remainingAmount'],2),
						'status':in_status,
						'cur':cur
						}
					invs_dic_due.append(inv_due)
				elif status == "Open":
					inv_open = {
						'id':dat['id'],
						'number':dat['number'],
						'shipToName':dat['shipToName'],
						'postingDate':dat['postingDate'],
						'dueDate':dat['dueDate'],
						'due_days':due_days,
						'totalAmountExcludingTax': round(dat['totalAmountExcludingTax'],2),
						'totalTaxAmount': round(dat['totalTaxAmount'],2),
						'totalAmountIncludingTax': round(dat['totalAmountIncludingTax'],2),
						'remainingAmount': round(dat['remainingAmount'],2),
						'status':in_status,
						'cur':cur
						}
					invs_dic_open.append(inv_open)
				else:
					inv = {
						'id':dat['id'],
						'number':dat['number'],
						'shipToName':dat['shipToName'],
						'postingDate':dat['postingDate'],
						'dueDate':dat['dueDate'],
						'due_days':due_days,
						'totalAmountExcludingTax': round(dat['totalAmountExcludingTax'],2),
						'totalTaxAmount': round(dat['totalTaxAmount'],2),
						'totalAmountIncludingTax': round(dat['totalAmountIncludingTax'],2),
						'remainingAmount': round(dat['remainingAmount'],2),
						'status':in_status,
						'cur':cur
						}
					invs_dic.append(inv)

			
		invs_dic_all = []
		for inv in invs_dic_due:
			invs_dic_all.append(inv)
		for inv in invs_dic_open:
			invs_dic_all.append(inv)
		for inv in invs_dic:
			invs_dic_all.append(inv)

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_invoices':invs_dic_all
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'],url_path='get_invoices/(?P<id>[^/.]+)')
	def get_invoice(self, request,id=None):

		print('----------get_invoice---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_invoice/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()


		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$expand":'salesInvoiceLines'}
		else:
			param = {"Tenant":tenant.tenant_id,"$expand":'salesInvoiceLines'}
		header = {"Content-Type":"application/json"}
		dat = call_BC(rq = api_request,api_type='bcv2',api='salesInvoices('+id+')', tenant=tenant,param=param,method ='get',view='invoice',header=header)

		if 'error' in dat:
			contant ={'response':{'code':HTTP_404_NOT_FOUND,'msg':'Not found'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)
		else:
			inv_lines_dic = []
			l_index = 1
			for invline in dat['salesInvoiceLines']:
				if invline['lineDetails']:
					item_no =invline['lineDetails']['number']
				else:
					item_no = None
				inv_line_dic ={
					'key':l_index,
					'lineType':invline['lineType'],
					'itemNumber':item_no,
					'description':invline['description'],
					'unitPrice':invline['unitPrice'],
					'quantity':invline['quantity'],
					'discountAmount':invline['discountAmount'],
					'amountExcludingTax':invline['netAmountIncludingTax'],
				}
				inv_lines_dic.append(inv_line_dic)
				l_index += 1

			due_date = datetime.strptime(dat['dueDate'], "%Y-%m-%d").date()
			if due_date <  date.today() and float(dat['remainingAmount']) > 0:
				status = "Due"
				due_days = abs((date.today() - due_date).days)
			else:
				status = "Open"
				due_days = None
			if dat['status'] == "Open":
				in_status = status
			else:
				in_status = dat['status']

			if dat['currencyCode'] == None or dat['currencyCode'] =='':
				cur = 'MVR'
			else:
				cur = dat['currencyCode']

			# get PDF
			if tenant.tenant_id == 'None':
				param = {"$filter":"No eq '"+dat['number'] + "'"}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"No eq '"+dat['number'] + "'"}
			header = {"Content-Type":"application/json"}
			data1 = call_BC(rq = api_request,api_type='piurl',api='SalesInvoicePDFs', tenant=tenant,param=param,method ='get',view='invoice',header=header)
			print(data1)
			if 'value' in data1:
				for data11 in data1['value']:
					if 'sales_invoice' in data11:
						file = settings.MEDIA_ROOT+'/'+ data11['No'].replace('/','-') + '-' +'.pdf'
						with open(file, 'wb') as f:
							f.write(base64.b64decode(data11['sales_invoice']))
						url_pdf = os.path.join(settings.MEDIA_URL,data11['No'].replace('/','-')+'-' +'.pdf')
						download_url = 'https://'+ get_current_site(request).domain+url_pdf
					else:
						download_url = ''
			else:
				download_url = ''
			 
			inv_dic = {
				'id':dat['id'],
				'number':dat['number'],
				'shipToName':dat['shipToName'],
				'postingDate':dat['postingDate'],
				'dueDate':dat['dueDate'],
				'due_days':due_days,
				'totalAmountExcludingTax': dat['totalAmountExcludingTax'],
				'totalTaxAmount': dat['totalTaxAmount'],
				'totalAmountIncludingTax': dat['totalAmountIncludingTax'],
				'remainingAmount': dat['remainingAmount'],
				'status':in_status,
				'cur':cur,
				'download_url': download_url,
				'invoice_lines':inv_lines_dic
			}
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_invoice':inv_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'])
	def get_orders(self, request):
		print('----------get_orders---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_orders/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant
		if tenant.tenant_id == 'None':
			param = {"$filter":"billToCustomerNumber eq '"+login_user.first_name+"'","$expand":'salesOrderLines',"$orderby":'id desc'}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"billToCustomerNumber eq '"+login_user.first_name+"'","$expand":'salesOrderLines',"$orderby":'id desc'}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='piurl',api='salesOrders', tenant=tenant,param=param,method ='get',view='orders',header=header)
		
		invs_dic = []
		for dat in data['value']:
			if dat['status'] == "Draft":
				or_status = "Open"
			elif dat['status'] == "Open":
				or_status = "Released"
			elif dat['status'] == "In Review":
				or_status = "Pending Approval"
			else:
				or_status =  dat['status']
			if dat['currencyCode'] == None or dat['currencyCode'] =='':
				cur = 'MVR'
			else:
				cur = dat['currencyCode']
			inv_dic = {
				'id':dat['id'],
				'number':dat['number'],
				'shipToName':dat['sellToAddressLine1'],
				'shipping':dat['shipToAddressLine1'],
				'po_number':dat['yourReference'],
				'postingDate':dat['postingDate'],
				'totalAmountExcludingTax': dat['totalAmountExcludingTax'],
				'totalTaxAmount': dat['totalTaxAmount'],
				'totalAmountIncludingTax': dat['totalAmountIncludingTax'],
				'status':or_status,
				'cur':cur,
				'Transaction_Type':dat['Transaction_Type']
			}
			invs_dic.append(inv_dic)
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_orders':invs_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'],url_path='get_orders/(?P<id>[^/.]+)')
	def get_order(self, request,id=None):
		print('----------get_order---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_order/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$expand":'salesOrderLines'}
		else:
			param = {"Tenant":tenant.tenant_id,"$expand":'salesOrderLines'}
		header = {"Content-Type":"application/json"}
		dat = call_BC(rq = api_request,api_type='piurl',api='salesOrders('+id+')', tenant=tenant,param=param,method ='get',view='order',header=header)
		if 'error' in dat:
			contant ={'response':{'code':HTTP_404_NOT_FOUND,'msg':'Not found'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_404_NOT_FOUND)
		else:
			inv_lines_dic = []
			l_index = 1
			for invline in dat['salesOrderLines']:
				item_no =invline['lineObjectNumber']

				inv_line_dic ={
					'key':l_index,
					'lineType':invline['lineType'],
					'itemNumber':item_no,
					'description':invline['description'],
					'unitPrice':invline['unitPrice'],
					'quantity':invline['quantity'],
					'discountAmount':invline['discountAmount'],
					'amountExcludingTax':invline['netAmountIncludingTax'],
				}
				inv_lines_dic.append(inv_line_dic)
				l_index +=1
			if dat['status'] == "Draft":
				or_status = "Open"
			elif dat['status'] == "Open":
				or_status = "Released"
			elif dat['status'] == "In Review":
				or_status = "Pending Approval"
			else:
				or_status =  dat['status']

			if dat['currencyCode'] == None or dat['currencyCode'] =='':
				cur = 'MVR'
			else:
				cur = dat['currencyCode']

			inv_dic = {
				'id':dat['id'],
				'number':dat['number'],
				'notes':dat['sellToAddressLine1'],
				'shipping_name':dat['shipToName'],
				'shipping_address':dat['shipToAddressLine1'],
				'po_number':dat['yourReference'],
				'postingDate':dat['postingDate'],
				'totalAmountExcludingTax': dat['totalAmountExcludingTax'],
				'totalTaxAmount': dat['totalTaxAmount'],
				'totalAmountIncludingTax': dat['totalAmountIncludingTax'],
				'status':or_status,
				'cur':cur,
				'Transaction_Type':dat['Transaction_Type'],
				'order_lines':inv_lines_dic
			}

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_invoice':inv_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)



	@action(detail=False, methods=['get'])
	def get_items(self, request):
		print('----------get_items---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_items/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant
		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='bcv2',api='items', tenant=tenant,param=param,method ='get',view='items',header=header)
		items_dic = []
		for dat in data['value']:
			inv_dic = {
				'id':dat['id'],
				'number':dat['number'],
				'displayName':dat['displayName'],
				'inventory':dat['inventory'],
				'unitCost':dat['unitCost']
			}
			items_dic.append(inv_dic)
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_orders':items_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['post'])
	def make_order(self, request):
		print('----------make_order---------')
		api_request = ApiRequest()
		api_request.url ='/customers/make_order/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant
		items = request.data.get('items')
		shipToName = request.data.get('shipToName')
		po_number = request.data.get('po_number')
		shipping = request.data.get('shipping')
		slip = request.data.get('file')
		if str(type(items)) != "<class 'list'>":
			items = json.loads(items)		

		if not items and not shipToName:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Required infomation not provided'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		header = {"Content-Type":"application/json"}
		data_cust = call_BC(rq = api_request,api_type='bcv2',api='customers('+login_user.last_name+')', tenant=tenant,param=param,method ='get',view='make_order',header=header)

		if data_cust['currencyCode'] == None or data_cust['currencyCode'] == "":
			cur = 'MVR'
		else:
			cur = data_cust['currencyCode']


		senddata = {"customerNumber":login_user.first_name,"sellToAddressLine1":shipToName,"currencyCode": cur,"ShipToCode": shipping,"yourReference":po_number,"Transaction_Type":'CP'}
		header = {"Content-Type":"application/json"}
		print(senddata)
		data_order = call_BC(rq = api_request,api_type='piurl',api='salesOrders', tenant=tenant,param=param,method ='post',view='make_order',header=header,body=json.dumps(senddata))
		print(data_order)
		if 'error' in data_order:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'There is an issue with you account. Please contact '+tenant.name+'.'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		for item in items:
			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			senddata = {"itemId":item['itemId'],"lineType":"Item","quantity":int(item['quantity']),}
			header = {"Content-Type":"application/json"}
			data = call_BC(rq = api_request,api_type='bcv2',api='salesOrders('+ data_order['id']+')/salesOrderLines', tenant=tenant,param=param,method ='post',view='make_order',header=header,body=json.dumps(senddata))
		

		if tenant.tenant_id == 'None':
			param = {"$expand":"salesOrderLines"}
		else:
			param = {"Tenant":tenant.tenant_id,"$expand":"salesOrderLines"}
		header = {"Content-Type":"application/json"}
		dat = call_BC(rq = api_request,api_type='bcv2',api='salesOrders('+ data_order['id']+')', tenant=tenant,param=param,method ='get',view='make_order',header=header)

		order_lines_dic = []
		l_index = 1
		for invline in dat['salesOrderLines']:
			if invline['lineDetails']:
				item_no =invline['lineDetails']['number']
			else:
				item_no = None
			inv_line_dic ={
				'key':l_index,
				'lineType':invline['lineType'],
				'itemNumber':item_no,
				'description':invline['description'],
				'unitPrice':invline['unitPrice'],
				'quantity':invline['quantity'],
				'discountAmount':invline['discountAmount'],
				'amountExcludingTax':invline['netAmountIncludingTax'],
			}
			order_lines_dic.append(inv_line_dic)
			l_index +=1
		inv_dic = {
			'id':dat['id'],
			'number':dat['number'],
			'shipToName':dat['shipToName'],
			'postingDate':dat['postingDate'],
			'totalAmountExcludingTax': dat['totalAmountExcludingTax'],
			'totalTaxAmount': dat['totalTaxAmount'],
			'totalAmountIncludingTax': dat['totalAmountIncludingTax'],
			'status':dat['status'],
			'shippingPostalAddress':dat['shippingPostalAddress'],
			'order_lines':order_lines_dic
		}
		
		if 'id' in dat and slip:
			payment_id = dat['id']

			if slip.content_type in ['application/pdf','image/jpeg','image/png','image/jpg']:
				file = settings.MEDIA_ROOT+'/'+ slip.name
				destination = open(file, 'wb+')
				for chunk in slip.chunks():
					destination.write(chunk)
				destination.close()

				param = {}
				if tenant.tenant_id == 'None':
					param = {}
				else:
					param = {"Tenant":tenant.tenant_id}
				senddata = {"parentId":payment_id,"fileName":file}
				header = {"Content-Type":"application/json"}
				data = call_BC(rq = api_request,api_type='bcv2',api='attachments', tenant=tenant,param=param,method ='post',view='make_order',header=header,body=json.dumps(senddata))

				if tenant.tenant_id == 'None':
					param = {"$filter":"parentId eq "+data['parentId']+" and id eq " +data['id']}
				else:
					param = {"Tenant":tenant.tenant_id,"$filter":"parentId eq "+data['parentId']+" and id eq " +data['id']}
				data = call_BC(rq = api_request,api_type='bcv2',api='attachments', tenant=tenant,param=param,method ='get',view='make_order',header=header)

				parentId  = data['value'][0]['parentId']
				img_id  = data['value'][0]['id']
				etag  = data['value'][0]['@odata.etag'][2:]

				with open(file, 'rb') as f:
					file_data = f.read()

				param = {}
				if tenant.tenant_id == 'None':
					param = {}
				else:
					param = {"Tenant":tenant.tenant_id}
				header = {"If-Match":etag}
				data = call_BC(rq = api_request,api_type='bcv2',api='attachments(parentId='+parentId+',id='+img_id+')/content', tenant=tenant,param=param,method ='patch',view='make_order',header=header,body=file_data)

			else:
				contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'File not accepted'}}
				return Response(contant,status=HTTP_400_BAD_REQUEST)


		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_order':inv_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)



	@action(detail=False, methods=['post'], parser_classes =[MultiPartParser])
	def make_payment(self, request):
		print('----------make_payment---------')
		api_request = ApiRequest()
		api_request.url ='/customers/make_payment/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant
		slip = request.data.get('slip')
		amount = request.data.get('amount')
		invoice = request.data.get('invoices')
		comment = request.data.get('comment')
		if not amount or not slip:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Required infomation not provided'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)
		amount = float(amount)*-1

		if tenant.tenant_id == 'None':
			param = {"$filter":"code eq 'C-PORTAL'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"code eq 'C-PORTAL'"}
		header = {"Content-Type":"application/json"}
		journal = call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals', tenant=tenant,param=param,method ='get',view='make_payment',header=header)


		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		if invoice and comment:
			senddata = {"amount":float(amount),"customerNumber":login_user.first_name,"appliesToInvoiceId":invoice,"comment":comment}
		elif invoice:
			senddata = {"amount":float(amount),"customerNumber":login_user.first_name,"appliesToInvoiceId":invoice}
		elif comment:
			senddata = {"amount":float(amount),"customerNumber":login_user.first_name,"comment":comment}
		else:
			senddata = {"amount":float(amount),"customerNumber":login_user.first_name}
		data_payment = call_BC(rq = api_request,api_type='bcv2',api='customerPaymentJournals('+journal['value'][0]['id']+')/customerPayments', tenant=tenant,param=param,method ='post',view='make_payment',header=header,body=json.dumps(senddata))

		if 'id' in data_payment:
			payment_id = data_payment['id']

			if slip.content_type in ['application/pdf','image/jpeg','image/png','image/jpg']:
				file = settings.MEDIA_ROOT+'/'+ slip.name
				destination = open(file, 'wb+')
				for chunk in slip.chunks():
					destination.write(chunk)
				destination.close()
			else:
				contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'File not accepted'}}
				api_request.response =str(contant)[:2000]
				api_request.save()
				return Response(contant,status=HTTP_400_BAD_REQUEST)


			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			senddata = {"parentId":payment_id,"fileName":file}
			header = {"Content-Type":"application/json"}
			data = call_BC(rq = api_request,api_type='bcv2',api='attachments', tenant=tenant,param=param,method ='post',view='make_payment',header=header,body=json.dumps(senddata))


			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			senddata = {"parentId":payment_id,"fileName":file}
			header = {"Content-Type":"application/json"}
			data = call_BC(rq = api_request,api_type='bcv2',api='attachments', tenant=tenant,param=param,method ='post',view='make_payment',header=header,body=json.dumps(senddata))


			if tenant.tenant_id == 'None':
				param = {"$filter":"parentId eq "+data['parentId']+" and id eq " +data['id']}
			else:
				param = {"Tenant":tenant.tenant_id,"$filter":"parentId eq "+data['parentId']+" and id eq " +data['id']}
			data = call_BC(rq = api_request,api_type='bcv2',api='attachments', tenant=tenant,param=param,method ='get',view='make_payment',header=header)


			parentId  = data['value'][0]['parentId']
			img_id  = data['value'][0]['id']
			etag  = data['value'][0]['@odata.etag'][2:]
			with open(file, 'rb') as f:
				file_data = f.read()
			if tenant.tenant_id == 'None':
				param = {}
			else:
				param = {"Tenant":tenant.tenant_id}
			header = {"If-Match":etag}
			data = call_BC(rq = api_request,api_type='bcv2',api='attachments(parentId='+parentId+',id='+img_id+')/content', tenant=tenant,param=param,method ='patch',view='make_payment',header=header,body=file_data)

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'payment':{
				'postingDate': data_payment['postingDate'],
				'documentNumber': data_payment['documentNumber'],
				'amount': data_payment['amount'],
				'comment':data_payment['comment'],

			}
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)


	@action(detail=False, methods=['get'])
	def get_address(self, request):
		print('----------get_address---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_address/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$filter":"customerNumber eq '"+login_user.first_name+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"customerNumber eq '"+login_user.first_name+"'"}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='piurl',api='customerPortalShpAddress', tenant=tenant,param=param,method ='get',view='get_address',header=header)
		
		items_dic = []
		for dat in data['value']:
			inv_dic = {
				'id':dat['id'],
				'Code':dat['Code'],
				'name':dat['name'],
				'name2':dat['name2'],
				'address':dat['address'],
				'address2':dat['address2'],
				'City':dat['City'],
				'County':dat['County'],
				'phoneNo':dat['phoneNo'],
				'eMail':dat['eMail'],
			}
			items_dic.append(inv_dic)
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_addresses':items_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['post'])
	def new_address(self, request):
		print('----------new_address---------')
		api_request = ApiRequest()
		api_request.url ='/customers/new_address/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		name2 = request.data.get('name2')
		address = request.data.get('address')
		address2 = request.data.get('address2')
		City = request.data.get('City')
		County = (request.data.get('County'))
		eMail = request.data.get('eMail')
		phoneNo = request.data.get('phoneNo')
		Code = request.data.get('code')
		tenant = login_user.tenantuser.tenant


		if tenant.tenant_id == 'None':
			param = {"$filter":"customerNumber eq '"+login_user.first_name+"' and Code eq '"+ Code+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"customerNumber eq '"+login_user.first_name+"' and Code eq '"+ Code+"'"}
		header = {"Content-Type":"application/json"}
		check = call_BC(rq = api_request,api_type='piurl',api='customerPortalShpAddress', tenant=tenant,param=param,method ='get',view='new_address',header=header)


		if len(Code) > 10:
			contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Code cannot be greater than 10 chars'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		if 'value' in check:
			for a in check['value']:
				if 'id' in a:
					contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Code already exist'}}
					api_request.response =str(contant)[:2000]
					api_request.save()
					return Response(contant,status=HTTP_400_BAD_REQUEST)


		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		senddata = {"Code":Code,"customerNumber":login_user.first_name,"name2":name2,"address":address,"address2":address2,"City":City,"County":County,"phoneNo":phoneNo,"eMail":eMail}
		header = {"Content-Type":"application/json"}
		dat = call_BC(rq = api_request,api_type='piurl',api='customerPortalShpAddress', tenant=tenant,param=param,method ='post',view='new_address',header=header,body=json.dumps(senddata))

		inv_dic = {
			'id':dat['id'],
			'name':dat['name'],
			'name2':dat['name2'],
			'address':dat['address'],
			'address2':dat['address2'],
			'City':dat['City'],
			'County':dat['County'],
			'phoneNo':dat['phoneNo'],
			'eMail':dat['eMail'],
		}
		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'customer_addresse':inv_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)


	@action(detail=False, methods=['get'])
	def get_deliverynotes(self, request):
		print('----------get_deliverynotes---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_deliverynotes/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()
		from_date = request.GET.get('from_date')
		to_date = request.GET.get('to_date')

		if from_date == None or to_date == None:
			from_date = str(date.today().year)+'-'+str(date.today().month).rjust(2, '0')+'-01'
			to_date = str(date.today().year)+'-'+str(date.today().month).rjust(2, '0')+'-'+str(date.today().day).rjust(2, '0')

		print(from_date)
		print(to_date)

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = { "$filter":"customer_number eq '"+login_user.first_name+"' and source_document eq 'Sales Order' and destination_type eq 'Customer' and posting_date ge "+from_date+" and posting_date le "+to_date ,'$orderby':'posting_date desc'}
		else:
			param = {"Tenant":tenant.tenant_id, "$filter":"customer_number eq '"+login_user.first_name+"' and source_document eq 'Sales Order' and destination_type eq 'Customer' and posting_date ge "+from_date+" and posting_date le "+to_date,'$orderby':'posting_date desc'}
		header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='piurl',api='DeliveryNotes', tenant=tenant,param=param,method ='get',view='get_deliverynotes',header=header)
		
		items_dic = []
		key = 1
		if 'value'in data:
			for dat in data['value']:
				inv_dic = {
					'key':key,
					'No':dat['No'],
					'lineNo':dat['lineNo'],
					'sales_order_no':dat['sales_order_no'],
					'posting_date':dat['posting_date'],
					'pdf':'dn--'+str(dat['No'])

				}
				items_dic.append(inv_dic)
				key += 1


		if tenant.tenant_id == 'None':
			param = {"$filter":"customer_no eq '"+login_user.first_name+"' and Posting_Date ge "+from_date+" and Posting_Date le "+to_date,'$orderby':'Posting_Date desc'}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"customer_no eq '"+login_user.first_name+"' and Posting_Date ge "+from_date+" and Posting_Date le "+to_date,'$orderby':'Posting_Date desc'}
		print(param)
		data = call_BC(rq = api_request,api_type='piurl',api='SalesInvoices', tenant=tenant,param=param,method ='get',view='get_deliverynotes',header=header)

		if 'value'in data:
			for dat in data['value']:
				if 'GDN' in dat['filename']:
						inv_dic = {
							'key':key,
							'No':dat2['No'],
							'lineNo':dat2['lineNo'],
							'sales_order_no':dat['order_no'],
							'posting_date':dat['Posting_Date'],
							'pdf':'si--'+str(dat2['No'])
						}
						items_dic.append(inv_dic)
						key += 1

		print(items_dic)

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'delivary_notes':items_dic
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

	@action(detail=False, methods=['get'])
	def get_deliverynotes_pdf(self, request):
		print('----------get_deliverynotesPDF---------')
		api_request = ApiRequest()
		api_request.url ='/customers/get_deliverynotes_pdf/'
		api_request.method ='get'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()
		filename = request.GET.get('filename')
		# print(filename)
		if filename == None:
			contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'file not found'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		login_user = request.user
		tenant = login_user.tenantuser.tenant

		if tenant.tenant_id == 'None':
			param = {"$filter":"No eq '"+filename[4:]+"'"}
		else:
			param = {"Tenant":tenant.tenant_id,"$filter":"No eq '"+filename[4:]+"'"}
		header = {"Content-Type":"application/json"}
		# print(filename[4:])
		if filename[:2] == 'dn':
			data1 = call_BC(rq = api_request,api_type='piurl',api='DeliveryNotePdfs', tenant=tenant,param=param,method ='get',view='get_deliverynotes',header=header)
			print(data1)
			if 'value' in data1:
				dat1  = data1['value'][0]
				file = settings.MEDIA_ROOT+'/'+ filename +'.pdf'
				with open(file, 'wb') as f:
					f.write(base64.b64decode(dat1['Delivery_note']))
				# url_pdf = os.path.join(settings.MEDIA_URL,filename+'.pdf')
				url_pdf = os.path.join(settings.MEDIA_URL,filename +'.pdf')
				full_url_csv = 'https://'+ get_current_site(request).domain+url_pdf
			else:
				contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'file not found'}}
				api_request.response =str(contant)[:2000]
				api_request.save()
				return Response(contant,status=HTTP_400_BAD_REQUEST)


		elif filename[:2] == 'si':
			data1 = call_BC(rq = api_request,api_type='piurl',api='SIDeliveryNotePdfs', tenant=tenant,param=param,method ='get',view='get_deliverynotes',header=header)
			fnd  =1
			if 'value' in data1:
				for dat2 in data1['value']:
					fnd = 1
					if 'GDN' in dat2['file_name']:
						file = settings.MEDIA_ROOT+'/'+ filename +'.pdf'
						with open(file, 'wb') as f:
							f.write(base64.b64decode(dat2['Delivery_note']))
						url_pdf = os.path.join(settings.MEDIA_URL,filename +'.pdf')
						full_url_csv = 'https://'+ get_current_site(request).domain+url_pdf
						fnd = 2

			if fnd == 1:
				contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'file not found'}}
				api_request.response =str(contant)[:2000]
				api_request.save()
				return Response(contant,status=HTTP_400_BAD_REQUEST)

		else:
			contant = {'response':{'code':HTTP_400_BAD_REQUEST,'msg':'file not found'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		contant = {'response':{'code':HTTP_200_OK,'msg':'Found'},
		'data':{
			'pdf':full_url_csv
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)

		# zip_file = open(file, 'rb')
		# response = HttpResponse(FileWrapper(zip_file), content_type='application/pdf')
		# response['Content-Disposition'] = 'attachment; filename="%s"' % filename+'.pdf'
		# return response


	@action(detail=False, methods=['post'])
	def request_credit_limit(self, request):
		print('----------Request Credit limit---------')
		api_request = ApiRequest()
		api_request.url ='/customers/request_credit_limit/'
		api_request.method ='post'
		api_request.param =json.dumps(request.GET)
		api_request.body =str(json.dumps(request.POST))[:250]
		api_request.save()

		login_user = request.user
		amount = request.data.get('amount')
		expiry_date = request.data.get('expiry_date')
		tenant = login_user.tenantuser.tenant

		if not amount or not expiry_date:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':'Required infomation not provided'}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		if tenant.tenant_id == 'None':
			param = {}
		else:
			param = {"Tenant":tenant.tenant_id}
		senddata = {"tempCreditLimit":int(amount),"tempCreditLimitDate":expiry_date}
		header = {"Content-Type":"application/json"}

		dat = call_BC(rq = api_request,api_type='piurl',api='customerPortalUsers('+login_user.last_name+')', tenant=tenant,param=param,method ='get',view='request_credit_limit',header=header)
		
		etag = dat['@odata.etag'][2:]
		header = {"If-Match":etag,"Content-Type":"application/json"}
		# data = call_BC(rq = api_request,api_type='piurl',api='customerPortalUsers(tempCreditLimit='+amount+',tempCreditLimitDate='+expiry_date+')/content', tenant=tenant,param=param,method ='patch',view='request_credit_limit',header=header)
		# header = {"Content-Type":"application/json"}
		data = call_BC(rq = api_request,api_type='piurl',api='customerPortalUsers('+login_user.last_name+')', tenant=tenant,param=param,method ='patch',view='request_credit_limit',header=header,body=json.dumps(senddata))
		
		if 'error' in data:
			contant ={'response':{'code':HTTP_400_BAD_REQUEST,'msg':data['error']['message']}}
			api_request.response =str(contant)[:2000]
			api_request.save()
			return Response(contant,status=HTTP_400_BAD_REQUEST)

		contant = {'response':{'code':HTTP_200_OK,'msg':'Requested'},
		'data':{
			'request_credit_limit':'ok'
			}
		}
		api_request.response =str(contant)[:2000]
		api_request.save()
		return Response(contant,status=HTTP_200_OK)
    

    
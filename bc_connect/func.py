from bc_connect.models import *
from requests.auth import HTTPBasicAuth
import requests,json
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string='InstrumentationKey=8bdb789a-9888-49c8-b919-0c85c2f4e49e')
)
	

def refresh_token(tenant):
	auth_url = (TenantApi.objects.filter(tenant =tenant,name = 'oauth').first()).baseurl
	oauth_body = {
	'client_id':tenant.tenant_user,
	'client_secret':tenant.key,
	'grant_type':'client_credentials',
	'scope':tenant.scope,
	}
	response = requests.post(auth_url, data=(oauth_body))
	res_j  = response.json()
	token  = res_j['token_type']+ ' ' + res_j['access_token']
	tenant.token = token
	tenant.save()


def call_BC(rq = None,api_type=None,api=None,tenant=None,param=None,method=None,view=None,body=None,header=None):
	tenantapi = TenantApi.objects.filter(tenant =tenant,name = api_type).first()
	if tenant.auth_type == 'Key':
		auth=HTTPBasicAuth(tenant.tenant_user, tenant.key)
	elif tenant.auth_type == 'Oauth': 
		auth=None
		if header:
			header['Authorization'] = tenant.token
		else:
			header  = {
				'Authorization':tenant.token
			}
		

	url  = tenantapi.baseurl.replace('{company_id}',tenant.company_id) +api
	print(url)
	properties = {'custom_dimensions': {'url': url, 'method': method, 'header':str(header),'params':str(param),'body':str(body) , 'App':tenant.app_type}}

	if method =="get":
		response = requests.get(url, auth=auth,params=param,data=body,headers=header)
		if response.status_code == 401 and tenant.auth_type == 'Oauth':
			refresh_token(tenant)
			header['Authorization'] = tenant.token
			response = requests.get(url, auth=auth,params=param,data=body,headers=header)
		try:
			data = response.json()
		except Exception as e:
			data = response.text

	elif method =="post":
		response = requests.post(url, auth=auth,params=param,data=body,headers=header)
		if response.status_code == 401 and tenant.auth_type == 'Oauth':
			refresh_token(tenant)
			header['Authorization'] = tenant.token
			response = requests.post(url, auth=auth,params=param,data=body,headers=header)

		try:
			data = response.json()
		except Exception as e:
			data = response.text

	elif method =="patch":

		response = requests.patch(url, auth=auth,headers=header,params=param,data=body)
		if response.status_code == 401 and tenant.auth_type == 'Oauth':
			refresh_token(tenant)
			header['Authorization'] = tenant.token
			response = requests.patch(url, auth=auth,headers=header,params=param,data=body)
		try:
			data = response.json()
		except Exception as e:
			data = response.text
			
	elif method =="put":
		response = requests.put(url, auth=auth,params=param,data=body,headers=header)
		if response.status_code == 401 and tenant.auth_type == 'Oauth':
			refresh_token(tenant)
			header['Authorization'] = tenant.token
			response = requests.put(url, auth=auth,params=param,data=body,headers=header)
		try:
			data = response.json()
		except Exception as e:
			data = response.text

	if response.status_code < 200 or response.status_code > 299:
		print(properties)
		print(response.json())
		logger.error(response.json(), extra=properties)

	call = ApiTraffic()
	call.ApiRequest=rq
	call.api=url
	call.view = view
	call.method = method
	call.param = param
	if body:
		body = str(body)[:250]
	call.body = body
	call.response = str(data)[:2000]
	call.save()
	return data




def call_BC_v2(rq = None,api_type=None,api=None,tenant=None,param=None,method=None,view=None,body=None,header=None,response_type='json'):

	tenantapi = TenantApi.objects.filter(tenant =tenant,name = api_type).first()
	url  = tenantapi.baseurl.replace('{company_id}',tenant.company_id) +api

	if tenant.auth_type == 'Key':
		auth=HTTPBasicAuth(tenant.tenant_user, tenant.key)
		print(1)
		print(tenant.name)
	elif tenant.auth_type == 'Oauth': 
		print(2)
		print(tenant.name)
		auth=None
		auth_url = (TenantApi.objects.filter(tenant =tenant,name = 'oauth').first()).baseurl
		oauth_body = {
		'client_id':'c4ce0e7b-cd12-468b-be89-79979beadfae',
		'client_secret':'2H58Q~ZbzMQPlVthbnvo4.dHmg9Q_L1mknfqXcH_',
		'grant_type':'client_credentials',
		'scope':'https://api.businesscentral.dynamics.com/.default',
		}
		response = requests.get(auth_url, auth=auth,params=param,data=json.dumps(oauth_body),headers=header)
		print(response.json())

	print(url)
	properties = {'custom_dimensions': {'url': url, 'method': method, 'header':str(header),'params':str(param),'body':str(body) , 'App':tenantapi.tenant.app_type}}

	if method =="get":
		response = requests.get(url, auth=auth,params=param,data=body,headers=header)

	elif method =="post":
		response = requests.post(url, auth=auth,params=param,data=body,headers=header)

	elif method =="patch":
		response = requests.patch(url, auth=auth,params=param,data=body,headers=header)
			
	elif method =="put":
		response = requests.put(url, auth=auth,params=param,data=body,headers=header)

	if response.status_code < 200 or response.status_code > 299:
		logger.error(response.json(), extra=properties)


	if response_type == 'json' or response_type == None:
		try:
			data = response.json()
		except Exception as e:
			data = response.text
	elif response_type == 'response':
		data = response


	call = ApiTraffic()
	call.ApiRequest=rq
	call.api=url
	call.view = view
	call.method = method
	call.param = param
	if body:
		body = str(body)[:250]
	call.body = body
	call.response = str(data)[:2000]
	call.save()
	return data

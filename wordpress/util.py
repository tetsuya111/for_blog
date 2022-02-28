from . import api
import requests
from myutil import site
import json
import time
import pandas as pd

GET_ACTOR_URL="https://api.dmm.com/affiliate/v3/ActressSearch"

def _requests(url,apiid,affid,params={}):
	params={
		"api_id":apiid,
		"affiliate_id":affid,
		**params
	}
	res=requests.get(url,headers=site.HEADERS,params=params)
	return res.text

def getActors(apiid,affid,word="",n=10,params={}):
	params={
		"keyword":word,
		"hits":n,
		**params
	}
	text=_requests(GET_ACTOR_URL,apiid,affid,params)
	return json.loads(text)
def existActress(apiid,affid,name=""):
	data=getActors(apiid,affid,word=name,n=3)
	#print(name,data)
	return data["result"].get("actress")
av_actress="av_actress"
url="https://torino2019.com/fanza-capa/"
def getActressCategories(apiid,affid,url,start=1,pagenum=10**32):
	for data in api.getCategoriesN(url,start=start,n=pagenum):
		name=data["name"]
		#print("name",name)
		if existActress(apiid,affid,name):
			yield data
		time.sleep(1)
#"post_id","post_name","post_date","post_type","post_status","post_title","post_thumbnail","post_content","post_category","post_tags","value","maker","label","actress"
	


CONVERT_COLUMNS={
#for simple really csv importer
	"post_id":"id",
	"post_name":"",
	"post_date":"date",
	"post_status":"status",
	"post_title":"title",
}
def postCSV_2(csvpath,encoding="encoding"):
#for really simple csv importer format
	data=pd.read_csv(csvpath)
	columns=dict(enumerate(data.columns))
	for col in data.values:
		pass

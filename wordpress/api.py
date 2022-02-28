import urllib.parse as up
import requests
import json
import time
from myutil import site
import imghdr

GET_POSTS_PATH="wp-json/wp/v2/posts"
GET_CATEGORY_PATH="wp-json/wp/v2/categories"
GET_CATEGORY_PATH_BY_ID="wp-json/wp/v2/categories/{0}"
POST_MEDIA_PATH="wp-json/wp/v2/media"

def getPosts(url,page=1,params={}):
	params["page"]=page
	url=up.urljoin(url,GET_POSTS_PATH)
	res=requests.get(url,headers=site.HEADERS,params=params)
	if res.status_code // 100 != 2:
		return
	for data in json.loads(res.text):
		yield data
def getPostsN(url,start=1,n=1,params={}):
	for page in range(start,start+n):
		dataa=list(getPosts(url,page,params=params))
		if not dataa:
			break
		for data in dataa:
			yield data
		time.sleep(1)

def getCategories(url,page=1,params={}):
	params["page"]=page
	print(params)
	url=up.urljoin(url,GET_CATEGORY_PATH)
	res=requests.get(url,headers=site.HEADERS,params=params)
	if res.status_code // 100 != 2:
		return
	for data in json.loads(res.text):
		yield data
def getCategoriesN(url,start=1,n=1,params={}):
	for page in range(start,start+n):
		dataa=list(getCategories(url,page,params=params))
		if not dataa:
			break
		for data in dataa:
			yield data
		time.sleep(1)

def getCategoryByID(url,term_id):
	url=up.urljoin(url,GET_CATEGORY_PATH_BY_ID)
	url=url.format(term_id)
	res=requests.get(url,headers=site.HEADERS)
	if res.status_code // 100 != 2:
		return
	return json.loads(res.text)

def postMedia(apikey,url,imagedata):
	return
	url=up.urljoin(url,GET_CATEGORY_PATH_BY_ID)
	with site.TMP_F("wb+") as tmp:
		tmp.write(imagedata)
		tmp.seek(0)
		imgtype=imghdr.what(tmp.fname)
		if not imgtype:
			return None
		mime=f"image/{imgtype}"
		files={"file":(fname,imagedata,mime)}
		data={
			"status":"post"
		}
		res=requests.post(url,headers=site.HEADERS,files=files,data=data)
		print(res.text)
if __name__ == "__main__":
	url="https://torino2019.com/fanza-capa/"
	for data in getCategoriesN(url,n=30):
		print(json.dumps(data,ensure_ascii=False,indent=2))

import pandas as pd
from . import twitterbot as tb
from . import api
from myutil import site
import requests
import time
from bs4 import BeautifulSoup as bs
import urllib.parse as up

def toimagefile(imgurl):
	res=requests.get(imgurl,headers=site.HEADERS)
	fname=site.TMP_F.getfname()
	with open(fname,"wb") as f:
		f.write(res.content)
	return fname

class Tweet1(tb.Tweet):
	#tweet url of blog
	@staticmethod
	def make(title,url,tags=[],imgurls=[]):
		def toimagefiles(imgurls):
			for imgurl in imgurls:
				yield toimagefile(imgurl)
				time.sleep(1)
		tags="\n".join(map(lambda s:"#"+str(s),tags))
		text=title+"\n\n"+tags+"\n\n"+url
		imagefiles=toimagefiles(imgurls)
		return Tweet1(text,imagefiles=imagefiles)
	@staticmethod
	def make2(url,data):
		categories=data["categories"]
		categories=api.getCategories(url,params={"include":",".join(map(str,categories))})
		categories=list(map(lambda category:category["name"],categories))
		tags=categories
		return Tweet1.make(data["title"]["rendered"],data["link"],tags=tags)
	@staticmethod
	def readcsv(csvpath,encoding="utf8"):
		data=pd.read_csv(csvpath)
		for column in data.columns:
			tags=data[2].split(",")
			yield Tweet1.make(data[0],data[1],tags) 
class Tweet2(Tweet1):
	KIJIHAKOCHIRA=b'\xe8\xa8\x98\xe4\xba\x8b\xe3\x81\xaf\xe3\x81\x93\xe3\x81\xa1\xe3\x82\x89\xef\xbc\x81'.decode()
	@staticmethod
	def make(url,data,image_n=4):
		def getImgurls(soup):
			i=0
			for img in soup.select("img"):
				if i >= image_n:
					break
				src=img.get("src")
				if src:
					yield up.urljoin(url,src)
					i+=1
		content=data["content"]["rendered"]
		soup=bs(content,"html.parser")
		imgurls=list(getImgurls(soup))
		print("image urls",imgurls)
		categories=data["categories"]
		categories=api.getCategories(url,params={"include":",".join(map(str,categories))})
		categories=list(map(lambda category:category["name"],categories))
		tags=categories
		return Tweet1.make(data["title"]["rendered"],"",tags=tags,imgurls=imgurls)
	class Reply(tb.Tweet):
		@staticmethod
		def make(text,url):
			text=text+"\n\n"+url
			return Tweet1(text,replies=[])
	@staticmethod
	def make2(url,data,image_n=4):
		tw=Tweet2.make(url,data,image_n)
		rep=Tweet2.Reply.make(Tweet2.KIJIHAKOCHIRA,data["link"])
		tw.append(rep)
		return tw

import pandas as pd
from . import twitterbot as tb
from . import api

class Tweet1(tb.Tweet):
	#tweet url of blog
	@staticmethod
	def make(title,url,tags=[]):
		tags="\n".join(map(lambda s:"#"+str(s),tags))
		text=title+"\n\n"+tags+"\n\n"+url
		return Tweet1(text)
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

import kyodaishiki.__shell__ as ksh
import sys
from . import api
from . import tweet
from . import twitterbot as tb
import docopt
import zlib
import json
import random
import os

def hashurl(url):
	return zlib.adler32(url.encode())

class EnvKey:
	URL="URL"

class Docs:
	GET="""
	Usage:
		get (p|post) [(-s <start>)] [(-n <number>)]
	"""
	APPEND="""
	Usage:
		append (tw|tweet) 1 [(-s- <start>)] [(-n <number>)] [(-t <tags>)]
	"""
	SEARCH="""
	Usage:
		search (tw|tweet) <url>
	"""
	TWEET="""
	Usage:
		tweet (r|random) [(-p <params>)]
		tweet (r|random) 2 [(-p <params>)]
	
	Options:
		params : <key>:<vaue>,...
	"""
	TWEET_SHELL="""
	Usage:
		tweet_shell [<args>...]
	"""

class Command:
	GET=("G","GET")
	TWEET=("TW","TWEET")
	APPEND=("A","APPEND")
	SEARCH=("S","SEARCH")
	TWEET_SHELL=("TS","TWEET_SHELL")

class Shell(ksh.BaseShell3):
	def __init__(self,db):
		self.condb=db
		self.tweet_shell=tb.Shell(db)
		self.tweetdb=tb.TweetDB(db)
		self.tweetdb.createTable()
		super().__init__()
	@property
	def url(self):
		return self.environ.get(EnvKey.URL)
	def checkUrl(self,output=sys.stdout):
		if not self.url:
			print("Please set url.(set url <url>).",file=output)
			return False
		return True
	def _execQuery(self,query,output):
		if query.command in Command.GET:
			args=docopt.docopt(Docs.GET,query.args)
			if not self.checkUrl(output):
				return
			if args["p"] or args["post"]:
				start=int(args["<start>"] or 1)
				n=int(args["<number>"] or 1)
				for data in api.getPostsN(self.url,start,n):
					print(data,file=output)
		elif query.command in Command.TWEET:
			args=docopt.docopt(Docs.TWEET,query.args)
			if args["r"] or args["random"]:
				if not self.checkUrl(output):
					return
				bot=self.tweet_shell.current_bot
				if not bot:
					print("""
				please set bot.
					ts set bot ...
				""",file=output)
					return
				if args["2"]:
					if args["-p"]:
						params=args["<params>"]
						params=dict(map(lambda data:data.split(":",1),params.split(",")))
					else:
						params={}
					data=list(api.getPosts(self.url,params=params))
					print(data)
					if not data:
						return
					data=random.sample(data,1)[0]
					tw=tweet.Tweet2.make2(self.url,data)
					tw.do(bot)
					for imagefile in tw.imagefiles:
						os.remove(imagefile)
				else:
					if args["-p"]:
						params=args["<params>"]
						params=dict(map(lambda data:data.split(":",1),params.split(",")))
					else:
						params={}
					data=list(api.getPosts(self.url,params=params))
					print(data)
					if not data:
						return
					data=random.sample(data,1)[0]
					tw=tweet.Tweet1.make2(self.url,data)
					#print(tw,tw.text)
					tw.do(bot)

		elif query.command in Command.APPEND:
			args=docopt.docopt(Docs.APPEND,query.args)
			if not self.checkUrl(output):
				return
			if args["tw"] or args["tweet"]:
				if args["1"]:
					start=int(args["<start>"] or 1)
					n=int(args["<number>"] or 1)
					tags=args["<tags>"].split(",") if args["-t"] else []
					tags=(*tags,hashurl(self.url))
					for data in api.getPostsN(self.url,start,n):
						title=data["title"]["rendered"]
						link=data["link"]
						params={"include":",".join(map(str,sorted(data["categories"])))}
						#params={"inculde":data["categories"]}
						cdata=api.getCategoriesN(self.url,params=params)
						categories=list(map(lambda data_:data_["name"],cdata))
						tw=tweet.Tweet1.make(title,link,tags=categories)
						self.tweet_shell.tweetdb.append(text=tw.text,tags=tags)
		elif query.command in Command.SEARCH:
			args=docopt.docopt(Docs.SEARCH,query.args)
			if args["tw"] or args["tweet"]:
				url=args["<url>"]
				tag=hashurl(url)
				print(url,tag)
				for data in self.tweetdb.search(tags=[tag]):
					print(json.dumps(data,ensure_ascii=False,indent=2),file=output)
		elif query.command in Command.TWEET_SHELL:
			return self.tweet_shell.execQuery(ksh.Query(query.args),output)
		else:
			return super().execQuery(query,output)
	def execQuery(self,query,output):
		try:
			return self._execQuery(query,output)
		except SystemExit as e:
			print(e)
		except KeyboardInterrupt:
			pass
		except Exception as e:
			print(e)
	def close(self):
		super().close()
		self.condb.close()

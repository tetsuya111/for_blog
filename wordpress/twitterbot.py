import sqlite3
import kyodaishiki.__shell__ as ksh
import kyodaishiki._util as ku
import docopt
import re
import json
import time
import sys
import os
import random
import tweepy
import myutil
from functools import *


COLUMN=("name","consumer_key","consumer_secret","token","token_secret")


def _getbot1(token,token_secret,consumer_key,consumer_token):
	auth = tweepy.OAuth1UserHandler(consumer_key,consumer_token,token,token_secret)
	return tweepy.API(auth)
def _getbot2(token,token_secret,consumer_key,consumer_token):
	return tweepy.Client(
		access_token=token,
		access_token_secret=token_secret,
		consumer_key=consumer_key,
		consumer_secret=consumer_token
	)
	
def getbot(token,token_secret,consumer_key,consumer_token,version=1):
	if version == 2:
		return _getbot2(token,token_secret,consumer_key,consumer_token)
	return _getbot1(token,token_secret,consumer_key,consumer_token)

class BotDB:
	TABLE_NAME="twitter_bot_auth_data"
	def __init__(self,db):
		self.db=db
		self.cur=db.cursor()
	def createTable(self):
		self.cur.execute("create table if not exists {0} (name text,consumer_key text,consumer_secret text,token text,token_secret text)".format(self.TABLE_NAME))
	def append(self,name,consumer_key,consumer_secret,token,token_secret):
		self.cur.execute("insert into {0} values (?,?,?,?,?)".format(self.TABLE_NAME),(name,consumer_key,consumer_secret,token,token_secret))
	def list_name(self):
		return map(lambda data:data[0],self.cur.execute("select name from {0}".format(self.TABLE_NAME)))
	def _get(self,name):
		data=list(self.cur.execute("select * from {0} where name == ?".format(self.TABLE_NAME),[name]))
		return dict(zip(COLUMN,data[0])) if data else None
	def get(self,name,version=1):
		data=self._get(name)
		if not data:
			return None
		return getbot(
			data["token"],
			data["token_secret"],
			data["consumer_key"],
			data["consumer_secret"],
			version=version
			)
	def remove(self,name):
		self.cur.execute("delete from {0} where name == ?".format(self.TABLE_NAME),[name])
		self.db.commit()
	def close(self):
		self.db.close()



def count(s):
	i=0
	for c in s:
		if len(c.encode()) == 1:
			i+=1
		else:
			i+=2
	return i

def slice_(s,n=256):
	i=0
	res=""
	for c in s:
		if len(c.encode()) == 1:
			i+=1
		else:
			i+=2
		if i > n:
			return res
		res+=c
	return res

class Tweet:
	class Key:
		TEXT="text"
		IMAGEFILES="imagefiles"
		VIDEOFILE="videofile"
		REPLIES="replies"
		KWARGS="kwargs"
	def __init__(self,text="",imagefiles=[],videofile=None,replies=[],**kwargs):
		self.text=text
		self.imagefiles=imagefiles
		self.videofile=videofile
		self.replies=replies
		self.kwargs=kwargs
	def append(self,tweet):
		self.replies.append(tweet)
	def do(self,bot,reply_to_id=None):	
		media_ids=[]
		if self.imagefiles:
			for imagefile in self.imagefiles:
				res=bot.simple_upload(imagefile)
				media_ids.append(res.media_id)
		if self.videofile:
			res=bot.chunked_upload(self.videofile,file_type="video/mp4")
			media_ids.append(res.media_id)
		#media_ids=",".join(map(str,media_ids))
		media_ids=list(map(str,media_ids))
		status_id=bot.update_status(status=self.text,media_ids=media_ids,\
		in_reply_to_status_id=reply_to_id,**self.kwargs).id
		if not status_id:
			return False
		for reply in self.replies:
			reply.do(bot,reply_to_id=status_id)
		return True
	@staticmethod
	def make(data,replies=[]):
#data : {"text":<text>,"images_data":images_data,"video_data":video_data,replies:[<data>,...]}
		text=data.get(Tweet.Key.TEXT,"")
		imagefiles=data.get(Tweet.Key.IMAGEFILES,[])
		video_file=data.get(Tweet.Key.VIDEOFILE)
		replies__=map(lambda reply:Tweet.make(reply),data.get(Tweet.Key.REPLIES,[]))
		replies.extend(replies__)
		kwargs=data.get(Tweet.Key.KWARGS,{})
		return Tweet(text,imagefiles=imagefiles,videofile=videofile,replies=replies,**kwargs)

class TweetDB:
	COLUMN=("id","text","imagefiles","videofile","reply_to_id")
	TABLE_NAME="twitterbot_tweetdb_data"
	TAG_TABLE_NAME="twitterbot_tweetdb_tag_data"
	def __init__(self,db):
		self.db=db
		self.cur=db.cursor()
	def createMainTable(self):
		self.cur.execute("create table if not exists {0} (id integer primary key autoincrement,text text,imagefiles text,videofile text,reply_to_id int)".format(self.TABLE_NAME))
	def createTagTable(self):
		self.cur.execute("create table if not exists {0} (id int,tag text)".format(self.TAG_TABLE_NAME))
	def createTable(self):
		self.createMainTable()
		self.createTagTable()
	def append_data(self,text="",imagefiles=[],videofile="",reply_to_id=-1):
		imagefiles=",".join(imagefiles)
		self.cur.execute("insert into {0} (text,imagefiles,videofile,reply_to_id) values (?,?,?,?)".format(self.TABLE_NAME),(text,imagefiles,videofile,reply_to_id))
		data=list(self.cur.execute("select last_insert_rowid()"))
		return data[0][0] if data else None
	def append_tag(self,id_,tag):
		self.cur.execute("insert into {0} values (?,?)".format(self.TAG_TABLE_NAME),[id_,tag])
	def append(self,text="",imagefiles=[],videofile="",reply_to_id=-1,tags=[]):
		id_=self.append_data(text,imagefiles,videofile,reply_to_id)
		for tag in tags:
			self.append_tag(id_,tag)
		self.db.commit()
		return id_
	def toData(self,data):
		return dict(zip(self.COLUMN,data))
	def _get(self,id_):
		data=list(self.cur.execute("select * from {0} where id == ?".format(self.TABLE_NAME),[id_]))
		return self.toData(data[0]) if data else None
	def getTags(self,id_):
		for data in self.cur.execute("select tag from {0} where id == ?".format(self.TAG_TABLE_NAME),[id_]):
			yield data[0]
	def get(self,id_):
		data=self._get(id_)
		if not data:
			return None
		data["tags"]=list(self.getTags(id_))
		return data
	def _getReplies(self,id_):
		for data in self.cur.execute("select id from {0} where reply_to_id == ?".format(self.TABLE_NAME),[id_]):
			yield data[0]
	def get2(self,id_,tweet_class=Tweet):
		data=self.get(id_)
		replies=list(map(self.get2,self._getReplies(id_)))
		return tweet_class(
			text=data["text"],
			imagefiles=data["imagefiles"],
			videofile=data["videofile"],
			replies=replies
		)
	def _getTop(self,id_):
		data=self.get(id_)
		if not data:
			return None
		reply_to_id=data["reply_to_id"]
		return  self._getTop(reply_to_id) if reply_to_id else reply_to_id
	def _searchByTag(self,tag):
		data=map(lambda data:data[0],self.cur.execute("select id from {0} where tag like ?".format(self.TAG_TABLE_NAME),[tag]))
		return set(data)
	def _search(self,text="",tags=[]):
		res=[]
		res.append(sorted(map(lambda data:data[0],self.cur.execute("select id from {0} where text like ?".format(self.TABLE_NAME),[text]))))
		if tags:
			res.extend(sorted(map(lambda tag:self._searchByTag(tag),tags)))
		if not res:
			return []
		if len(res) == 1:
			return res[0]
		return reduce(myutil.and_,res)
	def search(self,text="%",tags=[]):
		return map(self.get,self._search(text,tags))
	def close(self):
		self.db.close()
	def __enter__(self):
		return self
	def __exit__(self,*args,**kwargs):
		self.close()

def inputTweet():
	text="\n".join(ku.inputUntilSeq("Text : "))
	imagefiles=list(ku.inputUntilSeq("ImageFile : "))
	videofile=input("VideoFile : ")
	tags=list(ku.inputUntilSeq("Tags : "))
	return {
		"text":text,
		"imagefiles":imagefiles,
		"videofile":videofile,
		"tags":tags
	}
class Docs:
	APPEND="""
	Usage:
		append (tw|tweet)
		append <botname> <consumer_key> <consumer_secret> <token> <token_secret>
	"""
	POST="""
	Usage:
		post <text>
	"""
	REMOVE="""
	Usage:
		remove <name>
	"""
	GET="""
	Usage:
		get <bot_name>
	"""
	SEARCH_DATA="""
	Usage:
		search_data (tw|tweet) [(-T <text>)] [(-t <tags>)]
	"""
	SEARCH="""
	Usage:
		search (tw|tweet) [(-T <text>)] [(-t <tags>)]
	"""
	LIST="""
	Usage:
		list [<name>]
	"""
	SET="""
	Usage:	
		set bot <name>
		set bot [(-v <version>)] <name>
	"""
	HELP="""
		append
		get
		upload
		list
		set
	"""

class Command:
	HELP=("H","HELP")
	APPEND=("A","APPEND")
	POST=("P","POST")
	REMOVE=("RM","REMOVE")
	GET=("G","GET")
	SEARCH=("S","SEARCH")
	UPLOAD=("UP","UL","UPLOAD")
	LIST=("LS","LIST")
	SET=["SET"]

class Shell(ksh.BaseShell3):	
	def __init__(self,db):
		self.db=db
		self.botdb=BotDB(db)
		self.tweetdb=TweetDB(db)
		self.cur=db.cursor()
		self.current_name=None
		self.current_bot=None
		self.current_version=None
		super().__init__()
		self.botdb.createTable()
		self.tweetdb.createTable()
	def _execQuery(self,query,output):
		if query.command in Command.HELP:
			print(Docs.HELP,file=output)
		elif query.command in Command.POST:
			args=docopt.docopt(Docs.POST,query.args)
			if not self.current_bot:
				print("don't setted bot.",file=output)
				return
				return False
			text=args["<text>"]
			self.current_bot.create_tweet(text=text)
		elif query.command in Command.APPEND:
		#append <botname> <consmer_key> <consumer_secret> <token> <token_secret>
			args=docopt.docopt(Docs.APPEND,query.args)
			if args["tw"] or args["tweet"]:
				tweet=inputTweet()
				id_=self.tweetdb.append(
					tweet["text"],
					tweet["imagefiles"],
					tweet["videofile"],
					tags=tweet["tags"]
				
				)
				print(id_,file=output)
			else:
				name=args["<botname>"]
				consumer_key=args["<consumer_key>"]
				consumer_token=args["<consumer_secret>"]
				token=args["<token>"]
				token_secret=args["<token_secret>"]
				self.botdb.append(name,consumer_key,consumer_token,token,token_secret)
				self.botdb.db.commit()
		elif query.command in Command.REMOVE:
			args=docopt.docopt(Docs.REMOVE,query.args)
			name=args["<name>"]
			self.db.remove(name)
		elif query.command in Command.GET:
			args=docopt.docopt(Docs.GET,query.args)
			name=args["<bot_name>"]
			data=self.botdb._get(name)
			print(json.dumps(data,indent=2),file=output)
		elif query.command in Command.SEARCH:
			args=docopt.docopt(Docs.SEARCH,query.args)
			for data in self.search_data(query.args,output):
					print(json.dumps(data,ensure_ascii=False,indent=2),file=output)
		elif query.command in Command.LIST:
			args=docopt.docopt(Docs.LIST,query.args)
			sname=args["<name>"] or ""
			for name in self.botdb.list_name():
				if re.match(sname,name):
					print(name,file=output)
		elif query.command in Command.SET:
			args=docopt.docopt(Docs.SET,query.args)
			if args["bot"]:
				name=args["<name>"]
				version=int(args["<version>"] or 1)
				bot=self.botdb.get(name,version=version)
				#print(bot.uriparts)
				if not bot:
					print('"{0} doesn\'t exist."'.format(name),file=output)
					return
				self.current_bot=bot
				self.current_name=name
				self.current_version=version
				print("Setted bot data.",file=output)
		else:
			return super().execQuery(query,output)
	def execQuery(self,query,output):
		try:
			return self._execQuery(query,output)
		except KeyboardInterrupt:
			pass
		except SystemExit as e:
			print(e)
	def search_data(self,args,output):
		args=docopt.docopt(Docs.SEARCH_DATA,args)
		if args["tw"] or args["tweet"]:
			text=args["<text>"] or ""
			text="%"+text+"%"
			tags=args["<tags>"].split(",") if args["-t"] else []
			for tweet in self.tweetdb.search(text,tags):
				yield tweet
	def close(self):
		super().close()
		self.db.close()

def crawl(bot,screen_name=None,user_id=None,once_n=100,depth=1,current_depth=0):
	if current_depth >= depth:
		return
	if not (screen_name or user_id):
		return
	if not user_id and screen_name:
		user=bot.get_user(screen_name=screen_name)
		user_id=user.id
	follows=bot.get_friend_ids(user_id=user_id)
	if len(follows) > once_n:
		follows=list(follows)[:once_n]
		random.shuffle(follows)
	for follow in follows:
		yield follow
		for follow__ in crawl(bot,user_id=follow,once_n=once_n,depth=depth,current_depth=current_depth+1):
			yield follow__
	

if __name__ == "__main__":
#t=getbot()
#t.statuses.update(status="Hello,World!")
	with Shell(sqlite3.connect("a.db")) as sh:
		sh.start()
		exit()
		sh.execQuery(ksh.Query(("set","bot","erotereneet")),sys.stdout)
		bot=sh.current_bot
		screen_name="ErotereNeet555"
		screen_name="zW0pm8aU0WDxJdN"
		for user_id in crawl(bot,screen_name=screen_name,once_n=3,depth=5):
			time.sleep(1)

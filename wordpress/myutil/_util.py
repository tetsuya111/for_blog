import os
import sys
import sqlite3


def _realpath(fname):
	return os.path.abspath( os.path.expanduser(os.path.expandvars(fname)))
def realpath(fname):	#expand vars of environ that you set may include vars of envrion.then you should expand twice.
	return _realpath(os.path.expandvars(fname))

def importPackage(dname):
	dname=realpath(dname)
	root,name=os.path.split(dname)
	sys.path.append(root)
	exec("import "+name)
importPKG=importPackage


def makeDB(db,table_name,columns,cols):
#columns={<typename>:<type>,...}
	size=len(columns)
	cur=db.cursor()
	columns=",".join(map(lambda key:key+" "+columns[key],columns))
	cur.execute("create table if not exists {0} ({1})".format(table_name,columns))
	hatenas=",".join(["?"]*size)
	for col in cols:
		try:
			cur.execute("insert into {0} values ({1})".format(table_name,hatenas),col)
			db.commit()
		except Exception as e:
			print(e,col)
			pass

def readDB(db,table_name):
	cur=db.cursor()
	return db.execute("select * from {0}".format(table_name))

def and_(data1,data2):	#data is sorted
	if type(data1) not in (list,tuple):
		data1=list(data1)
	if type(data2) not in (list,tuple):
		data2=list(data2)
	lenData1=len(data1)
	lenData2=len(data2)
	i=0
	j=0
	while i<lenData1 and j<lenData2:
		if data1[i]==data2[j]:
			yield data1[i]
			i+=1
			j+=1
		elif data1[i] > data2[j]:
			j+=1
		elif data1[i] < data2[j]:
			i+=1

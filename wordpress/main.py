from . import shell
import myutil
import sqlite3

DEF_DB_PATH=myutil.realpath("%USERPROFILE%\Documents\_wp_data.db")

def main():
	db=sqlite3.connect(DEF_DB_PATH)
	with shell.Shell(db) as sh:
		sh.start()

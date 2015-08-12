import cx_Oracle
from datetime import date, datetime, timedelta
import smtplib

#takes a cx_Oracle cursor object and returns current SYSDATE of associated db
#!!! can deprecate this and just use datetime.now()
def get_sysdate(cursor):
	cursor.execute('SELECT SYSDATE FROM ossdb.v_tg_pkt_loss WHERE rownum <= 1')
	return(cursor.fetchone()[0])

"""can deprecate, just print result of gen_hpl_alert"""
#given list of offenders (list of (trunk, percentage) tuples), prints list
def print_hpl_offenders(offenders):
	print("There are "+str(len(offenders))+" offenders with high packet loss on 15% or more completed calls:")
	print("---------------------------------------------------------------------------")
	
	#sort by percentage. switch to tup[0] to sort by trunk name
	offenders.sort(key=lambda tup: tup[1])

	#print list of trunks
	for pair in offenders:
		print("trunk name: " + str(pair[0]) + "\npercentage: " + "%.2f%%\n" % pair[1])
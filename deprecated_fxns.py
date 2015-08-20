import cx_Oracle
from datetime import date, datetime, timedelta
import smtplib

#takes a cx_Oracle cursor object and returns current SYSDATE of associated db
#!!! can deprecate this and just use datetime.now()
def get_sysdate(cursor):
	cursor.execute('SELECT SYSDATE FROM ossdb.v_tg_pkt_loss WHERE rownum <= 1')
	return(cursor.fetchone()[0])

#takes a cx_Oracle cursor object and prints the fields that are currently selected
def print_fields(cursor):
	desc = cursor.description
	print('--- FIELDS: ---')
	for row in desc:
		print(row[0])
	print()

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

#takes a cx_Oracle cursor object and prints the rows associated with high packet loss (hpl) DEPRECATED/TESTING
def print_hpl_rows(cursor):
	count = 0
	#print some example rows
	num_rows = int(input('Enter number of rows to print: '))

	for row in cursor:
		date 				= str(row[0])
		trunk 				= row[1]
		direction 			= str(row[2])
		attempts 			= row[3]
		answered 			= row[4]
		failed 				= row[5]
		otg_hlpkt_calls 	= row[6]
		dtg_hlpkt_calls 	= row[7]
		
		#if inbound, use OTG high packet loss calls. if outbound, use dtg high packet loss calls.
		total_hlpkt_calls	= otg_hlpkt_calls if direction == 'I' else dtg_hlpkt_calls

		hlpkt_ratio = 0
		if answered > 0:
			hlpkt_ratio = total_hlpkt_calls / answered

		if count < num_rows:
			print('trunk: ' 	+ str(trunk) + '\n' \
			'Date: ' 			+ date + '\n' \
			'direction: ' 		+ direction + '\n' \
			'completed calls: ' + str(answered) + '\n' \
			'otg_hlpkt_calls: ' + str(otg_hlpkt_calls) + '\n' \
			'dtg_hlpkt_calls: ' + str(dtg_hlpkt_calls) + '\n' \
			'percent of calls w/ high pkt loss: ' + str(hlpkt_ratio * 100) + '%\n')
			count += 1
		else:
			break
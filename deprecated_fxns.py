#delete this import if problems arise using python 3
from __future__ import division

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import HTML
import cx_Oracle
import smtplib

#takes a cx_Oracle cursor object and returns current SYSDATE of associated db
"""!!! can deprecate this and just use datetime.now()"""
def get_sysdate(cursor):
	cursor.execute('SELECT SYSDATE FROM ossdb.v_tg_pkt_loss WHERE rownum <= 1')
	return(cursor.fetchone()[0])

#takes a cx_Oracle cursor object and prints the fields that are currently selected STILL USEFUL!!
def print_fields(cursor):
	desc = cursor.description
	print('--- FIELDS: ---')
	count = 0
	for row in desc:
		print(str(count) + " " + row[0])
		count += 1
	print()

#given list of offenders (list of (trunk, percentage) tuples), prints list
"""can deprecate, just print result of gen_hpl_alert"""
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

#takes a message and recipients and sends via gmail SMTP
def send_email(subject, msg, recipients):

	#remember to change the time to the actual time the report is running for
	subject += "on GMT hour " + str(get_timeframe(datetime.now()))

	# this is the email I created for the alerts
	gmail_sender = 'traffic.summarizer.alerts@gmail.com'
	gmail_passwd = 'idtengineering123!'

	server = smtplib.SMTP_SSL('smtp.gmail.com:465')
	server.ehlo()
	server.login(gmail_sender, gmail_passwd)

	for recipient in recipients:

		body = '\r\n'.join(['To: %s' % recipient,
		                    'From: %s' % gmail_sender,
		                    'Subject: %s' % subject,
		                    '', msg])

		try:
		    server.sendmail(gmail_sender, [recipient], body)
		    print ('email sent to: ' + recipient)
		except:
		    print ('error sending mail')

	server.quit()

"""The following two functions were the original plaintextalert generator, switched from these to HTML"""

#given list of offenders (list of (trunk, percentage) tuples), generates PLAINTEXT ALERT MESSAGE
def gen_hpl_alert(offenders):
	
	msg = 'Alert: High packet loss ( >= 1% ) on greater than 15% of calls from the following ' + str(len(offenders)) + ' trunks:\n'

	#sort by percentage. switch to tup[0] to sort by trunk name
	offenders.sort(key=lambda tup: tup[3])

	for row in offenders:
		url = gen_url(get_timeframe(datetime.now()), row[0], row[4])
		msg += "\n" + url \
			+  "\ntrunk name: " 		+ str(row[0]) \
		 	+  "\n  completed calls: " 	+ str(row[1]) \
		 	+  "\n  total high packet loss calls: " 		+ str(row[2]) \
		 	+  "\n  percentage of completed calls with high packet loss: " + "%.2f%%\n" % row[3]

	return msg

#given list of offenders, generates alert message (deprecate?)
def gen_rteadv_alert(offenders):
	
	msg = 'Alert: High delay in signalling route-advanceable SIP response from the following ' + str(len(offenders)) + ' trunks:\n'

	#sort by time to generate route advanceable response
	offenders.sort(key=lambda tup: tup[4])

	for row in offenders:
		url = gen_url(get_timeframe(datetime.now()), row[0], 'O')
		msg += "\n" + url \
			+  "\ntrunk name: " 		+ str(row[0]) \
		 	+  "\n  attempts: " 		+ str(row[1]) \
		 	+  "\n  number of route-advanceable calls: " + str(row[2]) \
		 	+  "\n  percentage of attempts that were route-advanceable: " + "%.2f%%" % row[3] \
		 	+  "\n  avg time to signal route-advanceable SIP response: "  + "%.2f seconds\n" % row[4]

	return msg

"""------------"""
"""MAIN PROGRAM"""
"""------------"""

print("Current system time: " + str(datetime.now()))

#info for our db
host 	= 'ex01-scan.prod.idt.net'
port 	= 1521
service = 'ossdb.db.idt.net'

#connecting to cdrcsa database via service name
dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
db 		= cx_Oracle.connect('OSSREAD', 'oss2002read', dsn_tns)

#create a cursor object; basically an iterator for select queries.
curs 	= db.cursor()

#fetch rows to be examined then perform the High Packet Loss check
#curs.execute('SELECT * FROM ossdb.v_tg_calldur ORDER BY tstamp')
#curs.execute('SELECT * FROM ossdb.v_tg_pkt_loss')
#curs.execute('SELECT * FROM ossdb.v_tg_calldur')
curs.execute('SELECT * FROM ossdb.v_tg_tdra WHERE direction = \'O\' ORDER BY tdra_avg desc')
print_fields(curs)
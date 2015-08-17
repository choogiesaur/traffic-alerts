from __future__ import division
import cx_Oracle
from datetime import datetime, timedelta
import smtplib

#ex01-scan.prod-idt.net 	<- host
#ex02-scan.prod.idt.net
#ossdb.db.idt.net 			<- service_name

#takes a datetime.datetime object, translates to GMT, sets back 2 hours, and floors to nearest hour
def get_timeframe(date):
	#convert to gmt. keep as multiple lines to allow time zone flexibility
	gmt 	= date 	+ timedelta(hours=4)
	gmt_m2 	= gmt 	+ timedelta(hours=-2)
	return gmt_m2.replace(minute=0,second=0,microsecond=0)

#takes a cx_Oracle cursor object and prints the fields that are currently selected
def print_fields(cursor):
	desc = cursor.description
	print('--- FIELDS: ---')
	for row in desc:
		print(row[0])
	print()

#takes a cx_Oracle cursor object and prints the rows associated with high packet loss (hpl)
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

#given list of offenders (list of (trunk, percentage) tuples), generates alert message
def gen_hpl_alert(offenders):
	
	msg = 'Alert: High packet loss on greater than 15% of calls from the following ' + str(len(offenders)) + ' trunks:\n'

	#sort by percentage. switch to tup[0] to sort by trunk name
	offenders.sort(key=lambda tup: tup[1])

	for pair in offenders:
		msg += "\ntrunk name: " + str(pair[0]) + "\npercentage: " + "%.2f%%\n" % pair[1]

	return msg

#takes message and recipients and sends via gmail SMTP
def send_email(msg, recipients):

	subject = 'Traffic Summarizer Alerts: ' + str(datetime.now())

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

#takes a cx_Oracle cursor object and prints list of tg_id's with HPL above threshold. Also takes current 
def alert_pktloss(cursor):
	
	recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com', 'romel.khan@idt.net']

	#list of trunks with HPL on 15% or more of calls
	offenders 	= []

	#calculate time from which records will be fetched. OS time => GMT => 2 hours before => floored to last hour
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 				= row[0] #save as datetime obj, not string
		trunk 				= row[1]
		direction 			= str(row[2])
		completed 			= row[4]
		otg_hlpkt_calls 	= row[6]
		dtg_hlpkt_calls 	= row[7]
		
		#if inbound, use OTG high packet loss calls. if outbound, use dtg high packet loss calls.
		total_hlpkt_calls	= otg_hlpkt_calls if direction == 'I' else dtg_hlpkt_calls

		#only look at records from desired hour (2 hours before)
		if date == timeframe:
			
			#if 15% or more of calls have HPL, add to offenders list
			if (total_hlpkt_calls / completed) >= 0.15:
				offenders.append([trunk, (total_hlpkt_calls/completed) * 100])

	#print list of offenders
	alert = gen_hpl_alert(offenders)
	print(alert)
	send_email(alert, recipients)

"""------------"""
"""MAIN PROGRAM"""
"""------------"""

print(datetime.now())

#info for our db
host 	= 'ex01-scan.prod.idt.net'
port 	= 1521
service = 'ossdb.db.idt.net'

#connecting to cdrcsa database via service name
dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
db 		= cx_Oracle.connect('OSSREAD', 'oss2002read', dsn_tns)

#create a cursor object; basically an iterator for select queries.
curs 	= db.cursor()

#fetch rows to be examined
curs.execute('SELECT * FROM ossdb.v_tg_pkt_loss ORDER BY tstamp')

#print_fields(curs)
#print_hpl_rows(curs)
alert_pktloss(curs)

db.close()
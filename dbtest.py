#delete this import if using python 3
from __future__ import division

from datetime import datetime, timedelta
from tabulate import tabulate
import cx_Oracle
import smtplib

"""
NOTE: This was primarily developed under Python 3. It works on vetools01 with Python 2 and 
the __future__ import, but if any compatibility issues arise, just install the above packages,
delete the first line, and run on python 3.
"""

#ex01-scan.prod-idt.net 	<- host
#ex02-scan.prod.idt.net
#ossdb.db.idt.net 		<- service_name

#takes a datetime.datetime object in EST, translates to GMT, sets back 2 hours, and floors to nearest hour.
def get_timeframe(date):
	#convert to gmt. keep as multiple lines to allow time zone flexibility
	gmt 	= date 	+ timedelta(hours=4)
	gmt_m2 	= gmt 	+ timedelta(hours=-2)
	return gmt_m2.replace(minute=0,second=0,microsecond=0)

#given time, trunk generates the url for the trunk usage w/ dest page on traffic summarizer website
def gen_url(time, trunk, direction):

	#example: http://reports.idttechnology.com/traffic/tgdsum.psp?sdt=2015-08-20_10&edt=2015-08-20_11&otg=LEVEL3LAC

	year 	= str(time.year)
	month	= '0' + str(time.month)		if time.month 	< 10  else str(time.month)
	day		= '0' + str(time.day)		if time.day   	< 10  else str(time.day)
	s_hour 	= '0' + str(time.hour)		if time.hour  	< 10  else str(time.hour)
	e_hour	= '0' + str(time.hour+1)	if time.hour+1  < 10  else str(time.hour)

	url 	= "http://reports.idttechnology.com/traffic/tgdsum.psp?sdt=%s-%s-%s_%s&edt=%s-%s-%s_%s&otg=%s" \
			% (year, month, day, s_hour, year, month, day, e_hour, trunk)

	return url 

#takes message and recipients and sends via gmail SMTP
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

"""-------------------------------"""
"""Code for High Packet Loss alert"""
"""-------------------------------"""

#given list of offenders (list of (trunk, percentage) tuples), generates alert message
def gen_hpl_alert(offenders):
	
	msg = 'Alert: High packet loss ( >= 1% ) on greater than 15% of calls from the following ' + str(len(offenders)) + ' trunks:\n'

	#sort by percentage. switch to tup[0] to sort by trunk name
	offenders.sort(key=lambda tup: tup[3])

	for row in offenders:
		url = gen_url(get_timeframe(datetime.now()), row[0], row[4])
		msg += "\ntraffic summarizer URL: " + url
		msg += "\n  trunk name: " 		+ str(row[0]) \
		 	+  "\n  completed calls: " 	+ str(row[1]) \
		 	+  "\n  total high packet loss calls: " 		+ str(row[2]) \
		 	+  "\n  percentage of completed calls with high packet loss: " + "%.2f%%\n" % row[3]

	#msg += '\n' + tabulate(offenders, headers=['Trunk','Completed Calls','Total HPL Calls','Percentage'])

	return msg

#takes a cx_Oracle cursor object and prints list of trunks with HPL above threshold.
def alert_pktloss(cursor):
	
	recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com']
	#recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com', 'romel.khan@idt.net', 'richard.lee@idt.net']

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
				offenders.append([trunk, completed, total_hlpkt_calls, (total_hlpkt_calls/completed) * 100, direction])
				#				row[0]		row[1]	row[2]				row[3]								row[4]

	#print alert to terminal, then send email to recipients
	alert = gen_hpl_alert(offenders)
	print(alert)
	send_email('Alert: High Packet Loss ', alert, recipients)

"""--------------------------------"""
"""Code for Route-advanceable alert"""
"""--------------------------------"""

#given list of offenders (list of (trunk, percentage) tuples), generates alert message
def gen_rteadv_alert(offenders):
	
	msg = 'Alert: High delay in signalling route-advanceable SIP response from the following ' + str(len(offenders)) + ' trunks:\n'

	#sort by time to generate route advanceable response
	offenders.sort(key=lambda tup: tup[4])

	for row in offenders:
		msg += "\ntrunk name: " 		+ str(row[0]) \
		 	+  "\n  attempts: " 		+ str(row[1]) \
		 	+  "\n  number of route-advanceable calls: " + str(row[2]) \
		 	+  "\n  percentage of attempts that were route-advanceable: " + "%.2f%%" % row[3] \
		 	+  "\n  avg time to signal route-advanceable SIP response: "  + "%.2f seconds\n" % row[4]

	return msg

#takes a cx_Oracle cursor object and prints list of tg_id's with HPL above threshold. Also takes current 
def alert_rteadv(cursor):
	
	recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com']
	#recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com', 'romel.khan@idt.net', 'richard.lee@idt.net']

	#list of trunks with HPL on 15% or more of calls
	offenders 	= []

	#calculate time from which records will be fetched. OS time => GMT => 2 hours before => floored to last hour
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 				= row[0] #save as datetime obj, not string
		trunk 				= row[1]
		direction 			= str(row[2])
		attempts 			= row[3]
		answered			= row[4]
		#failed				= row[5]
		tdra_count			= row[8]
		#tdra_total			= row[9]
		tdra_avg			= row[10]

		#only look at records from desired hour (2 hours before)
		if date == timeframe:

			#minimum 100 route advanceable calls and >= 20% of all attempts are route advanceable,
			#if avg time to signal route advanceable sip response is >= 6 seconds, generate alert
			if (tdra_count / attempts) >= 0.20 and tdra_avg >= 6:
				offenders.append([trunk, attempts, tdra_count, (tdra_count / attempts) * 100 ,tdra_avg])

	#print alert to terminal, then send email to recipients
	alert = gen_rteadv_alert(offenders)
	print(alert)
	send_email('Alert: Route Advanceable SIP Response ', alert, recipients)

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

#"""
#fetch rows to be examined then perform the High Packet Loss check
curs.execute('SELECT * FROM ossdb.v_tg_pkt_loss ORDER BY tstamp')
alert_pktloss(curs)
#"""

"""
#fetch rows to be examined then perform the route advanceable check
curs.execute('SELECT * FROM ossdb.v_tg_tdra WHERE direction = \'O\' ORDER BY tdra_avg desc')
alert_rteadv(curs)
"""

#make sure to generate url for GMT. or clicking on it will give the report for 2 hours earlier (EST)
#print(gen_url(get_timeframe(datetime.now()), 'NPPINATCOMHT_Y'))

db.close()
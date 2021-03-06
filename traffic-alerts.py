#delete this import if problems arise using python 3
from __future__ import division

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import HTML
import cx_Oracle
import smtplib

"""
NOTE: This was primarily developed under Python 3. It works with Python 2 and 
the __future__ import, but if any compatibility issues arise, just install the above packages,
delete the first line, and run on python 3.
"""

#<HOSTNAME>	<- host
#<SERVICENAME> 	<- service_name

global_recipients = ['XXXXXXXX@blah.com', 'YYYYYYYY@blah.com']

#takes a datetime.datetime object in EST, translates to GMT, sets back 2 hours, and floors to nearest hour.
def get_timeframe(date):
	#convert to gmt. keep as multiple lines to allow time zone flexibility
	gmt 	= date 	+ timedelta(hours=4)
	gmt_m2 	= gmt 	+ timedelta(hours=-2)
	return gmt_m2.replace(minute=0,second=0,microsecond=0)

#given time, trunk, and inbound/outbound generates the url for the trunk usage w/ dest page on traffic summarizer website
def gen_url(time, trunk, direction):

	#example: http://reports.idttechnology.com/traffic/tgdsum.psp?sdt=2015-08-20_10&edt=2015-08-20_11&otg=LEVEL3LAC
	year 	= str(time.year)
	month	= '0' + str(time.month)		if time.month 	< 10  else str(time.month)
	day 	= '0' + str(time.day)		if time.day   	< 10  else str(time.day)
	s_hour 	= '0' + str(time.hour)		if time.hour  	< 10  else str(time.hour)
	e_hour	= '0' + str(time.hour+1)	if time.hour+1  < 10  else str(time.hour)
	
	summarizer_url 	= "<blah.com>"
	url 		= summarizer_url + "sdt=%s-%s-%s_%s&edt=%s-%s-%s_%s" \
			% (year, month, day, s_hour, year, month, day, e_hour)

	#append 'otg=' when carrier is inbound, 'dtg=' when carrier is outbound
	url 	+= ("&otg=" + trunk) if direction == 'I' else ("&dtg=" + trunk)
	return url 

#uses google SMTP to send html alert message
def send_html_email(subject, html, recipients):

	subject += "on GMT hour " + str(get_timeframe(datetime.now()))

	#email I created for the alerts. feel free to change, although only tested with gmail
	gmail_sender = 'gmail_acct'
	gmail_passwd = 'password'

	server = smtplib.SMTP_SSL('smtp.gmail.com:465')
	server.ehlo()
	server.login(gmail_sender, gmail_passwd)

	for recipient in recipients:

		msg 		= MIMEMultipart('alternative')
		msg['Subject'] 	= subject
		msg['From'] 	= gmail_sender
		msg['To'] 	= recipient

		# Record the MIME types of both parts - text/plain and text/html.
		#part1 = MIMEText(text, 'plain')
		part2 = MIMEText(html, 'html')
		msg.attach(part2)

		try:
		    server.sendmail(gmail_sender, [recipient], msg.as_string())
		    print ('  email sent to: ' + recipient)
		except:
		    print ('  error sending mail to: ' + recipient)

	server.quit()

"""-------------------------------"""
"""----High Packet Loss alert-----"""
"""-------------------------------"""

#given list of offenders (list of (trunk, percentage) tuples), generates alert as HTML TABLE
def gen_hpl_html(offenders):
	
	if len(offenders) == 0:
		return "No offenders for this hour."

	headers = ['Trunk', 'Completed Calls', 'High Packet Loss Calls', 'Percentage of calls with high packet loss', 'Direction', 'ALOC']

	#sort by descending percentage. switch to tup[0] to sort by trunk name
	offenders.sort(key=lambda tup: tup[3], reverse=True)

	#replace trunk name with clickable URL, format percentage
	for row in offenders:
		row[0] = HTML.link( row[0] , gen_url(get_timeframe(datetime.now()) , row[0] , row[4]))
		row[3] = "%.2f%%\n" % row[3]
		row[5] = "%.2f\n" % row[5]

	
	txt = 'Alert: High packet loss ( >= 1% ) on greater than 15% of calls from the following ' + str(len(offenders)) + ' trunks:\n'
	msg = txt + HTML.table([headers] + offenders)
	return msg

#takes a cx_Oracle cursor object and prints list of trunks with high packet loss above threshold.
def alert_pktloss(cursor):
	
	recipients = global_recipients

	#list of trunks with HPL on 15% or more of calls
	offenders 	= []

	#calculate time from which records will be fetched. OS time => GMT => 2 hours before => floored to last hour
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 		= row[0] #save as datetime obj, not string
		trunk 		= row[1]
		direction 	= str(row[2])
		completed 	= row[4]
		call_seconds	= row[6]
		otg_hlpkt_calls = row[8]
		dtg_hlpkt_calls = row[9]
		
		#if inbound, use OTG high packet loss calls. if outbound, use dtg high packet loss calls.
		total_hlpkt_calls = otg_hlpkt_calls if direction == 'I' else dtg_hlpkt_calls

		#only look at records from desired hour (2 hours before)
		if date == timeframe:
			
			#if 15% or more of calls have HPL, add to offenders list
			if (total_hlpkt_calls / float(completed)) >= 0.15:
				aloc = (call_seconds / float(60) ) / completed
				offenders.append([trunk, completed, total_hlpkt_calls, (total_hlpkt_calls/completed) * 100 , direction, aloc])
				#				row[0]		row[1]	row[2]				row[3]								row[4]

	#print alert to terminal, then send email to recipients
	print('\ngenerating high packet loss alert...')
	alert = gen_hpl_html(offenders)
	send_html_email('Alert: High Packet Loss ', alert, recipients)

"""--------------------------------"""
"""Route-advanceable response alert"""
"""--------------------------------"""

#given list of offenders, generates alert HTML for email
def gen_rteadv_html(offenders):

	if len(offenders) == 0:
		return "No offenders for this hour."
	
	headers = ['Trunk', 'Attempts', 'ASR', '# Route-advanceable Calls', 'Percentage of Attempts Route-advanceable', 'Average time to signal route-advanceable SIP response']

	#sort by time to generate route advanceable response
	offenders.sort(key=lambda tup: tup[5], reverse=True)

	for row in offenders:
		row[0] = HTML.link( row[0] , gen_url(get_timeframe(datetime.now()) , row[0] , 'O'))
		row[2] = "%.2f\n" % (row[2] / float(row[1])) #calculate ASR
		row[4] = "%.2f%%\n" % row[4]
		row[5] = "%.2f\n" % row[5]

	txt = 'Alert: High delay in signalling route-advanceable SIP response from the following ' + str(len(offenders)) + ' trunks:\n'
	msg = txt + HTML.table([headers] + offenders)
	return msg

#takes a cx_Oracle cursor object and prints list of trunks with high delay in signalling route-advanceable SIP response
def alert_rteadv(cursor):
	
	recipients = global_recipients

	#list of trunks that take too long to signal route advanceable SIP response
	offenders = []

	#calculate time from which records will be fetched. OS time => GMT => 2 hours before => floored to last hour
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 		= row[0] #save as datetime obj, not string
		trunk 		= row[1]
		attempts 	= row[3]
		answered	= row[4]
		tdra_count	= row[8]
		tdra_avg	= row[10]

		#only look at records from desired hour (2 hours before)
		if date == timeframe:

			#minimum 100 route advanceable calls and >= 20% of all attempts are route advanceable,
			#if avg time to signal route advanceable sip response is >= 6 seconds, generate alert
			if (tdra_count / attempts) >= 0.20 and tdra_avg >= 6:
				offenders.append([trunk, attempts, answered, tdra_count, (tdra_count / attempts) * 100 ,tdra_avg,])

	#print alert to terminal, then send email to recipients
	print('\ngenerating route advanceable alert...')
	alert = gen_rteadv_html(offenders)
	send_html_email('Alert: Route Advanceable SIP Response ', alert, recipients)

"""----------------------------"""
"""Code for Call Duration alert"""
"""----------------------------"""

def gen_calldur_html(offenders):

	if len(offenders) == 0:
		return "No offenders for this hour."
	
	headers = ['Trunk', 'Attempts', 'Completed Calls', 'ALOC', 'Calls under 30 sec', 'Calls under 1 min', 'Percentage Under 30s', 'Percentage Under 1m']

	for row in offenders:
		row[0] = HTML.link( row[0] , gen_url(get_timeframe(datetime.now()) , row[0] , row[6]))
		del row[6]
		row[3] = "%.2f\n" % row[3]
		row.append("%.2f%%\n" % ((row[4] / float(row[2])) * 100))
		row.append("%.2f%%\n" % ((row[5] / float(row[2])) * 100))

	#sort by percentage of completed calls under 30 seconds
	offenders.sort(key=lambda tup: tup[6], reverse=True)

	txt = 'Alert: High volume of calls with short duration from the following ' + str(len(offenders)) + ' trunks:\n'
	msg = txt + HTML.table([headers] + offenders)
	return msg

#takes a cx_Oracle cursor object and prints trunks with high volume of short-duration calls (< 30 sec, < 1min)
def alert_calldur(cursor):
	
	recipients = global_recipients
	offenders  = []
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 		= row[0]
		trunk 		= row[1]
		direction 	= row[2]
		attempts 	= row[3]
		answered 	= row[4]
		call_seconds	= row[5]
		dur_10s 	= row[7]
		dur_30s 	= row[8]
		dur_1m 		= row[9]

		#only look at records from desired hour (2 hours before)
		if date == timeframe and answered >= 1000:

			#add intervals to get total calls less than 30 seconds, less than 1 minute
			under_30s 	= dur_10s + dur_30s
			under_1m 	= dur_10s + dur_30s + dur_1m

			aloc = (call_seconds / float(60) ) / float(answered)

			if (under_30s / float(answered)) > 0.80 or (under_1m / float(answered)) > 0.95:
				offenders.append([trunk, attempts, answered, aloc, under_30s, under_1m, direction])

	print('\ngenerating call duration alert...')
	alert = gen_calldur_html(offenders)
	send_html_email('Alert: Short Call Duration ', alert, recipients)

"""------------"""
"""MAIN PROGRAM"""
"""------------"""

print("Current system time: " + str(datetime.now()))

#info for our db
host 	= 'HOSTNAME'
port 	= 'PORT'
service = 'SERVICENAME'

#connecting to cdrcsa database via service name
dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
db 		= cx_Oracle.connect('a','b','c')

#create a cursor object; basically an iterator for select queries.
curs 	= db.cursor()

#"""
#fetch rows to be examined then perform the High Packet Loss check
curs.execute('<HPL sql query>')
alert_pktloss(curs)
#"""

#"""
#fetch rows to be examined then perform the route advanceable check
curs.execute('<RTEADV sql query>')
alert_rteadv(curs)
#"""

#"""
#fetch rows to be examined then perform the route advanceable check
curs.execute('<CALLDUR sql query>')
alert_calldur(curs)
#"""

db.close()

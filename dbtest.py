import cx_Oracle
from datetime import date, datetime, timedelta

#ex01-scan.prod-idt.net 	<- host
#ex02-scan.prod.idt.net
#ossdb.db.idt.net 			<- service_name

#takes a cx_Oracle cursor object and returns current SYSDATE of associated db
#can deprecate this and just use datetime.now()
def get_sysdate(cursor):
	cursor.execute('SELECT SYSDATE FROM ossdb.v_tg_pkt_loss WHERE rownum <= 1')
	return(cursor.fetchone()[0])

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
		total_hlpkt_calls	= 0
		
		#if inbound, use OTG for number of high packet loss calls
		if direction == 'I':
			total_hlpkt_calls = otg_hlpkt_calls
		#if outbound, use DTG for number of high packet loss calls
		elif direction == 'O':
			total_hlpkt_calls = dtg_hlpkt_calls

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
			'ttl_hlpkt_calls: ' + str(total_hlpkt_calls) + '\n' \
			'percent of calls w/ high pkt loss: ' + str(hlpkt_ratio * 100) + '%\n')
			count += 1
		else:
			break

#takes a cx_Oracle cursor object and prints list of tg_id's with HPL above threshold. Also takes current 
def check_pktloss(cursor):
	
	#list of tg_id's with HPL on 15% or more of calls
	offenders 	= []

	#calculate time from which records will be fetched. OS time => GMT => 2 hours before
	timeframe = get_timeframe(datetime.now())

	for row in cursor:

		date 				= row[0] #save as datetime obj, not string
		trunk 				= row[1]
		direction 			= str(row[2])
		completed 			= row[4]
		otg_hlpkt_calls 	= row[6]
		dtg_hlpkt_calls 	= row[7]
		total_hlpkt_calls	= 0

		#only look at records from desired hour
		if date == timeframe:

			if direction == 'I':
				total_hlpkt_calls = otg_hlpkt_calls

			elif direction == 'O':
				total_hlpkt_calls = dtg_hlpkt_calls
			
			#after there are at least <100> completed calls: if more than 15% of calls have HPL, add to offenders list
			if completed > 100 and total_hlpkt_calls / completed > 0.15:
				offenders.append([trunk, (total_hlpkt_calls/completed) * 100])

	print("There are "+str(len(offenders))+" offenders with high packet loss on 15% or more completed calls:")
	print("---------------------------------------------------------------------------")
	
	#print list of tg_id's
	for pair in offenders:
		print("trunk name: " + str(pair[0]) + "\npercentage: " + "%.2f%%\n" % pair[1])

#info for our db
host 	= 'ex01-scan.prod.idt.net'
port 	= 1521
service = 'ossdb.db.idt.net'

#connecting to cdrcsa database via service name
dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
db 		= cx_Oracle.connect('OSSREAD', 'oss2002read', dsn_tns)

#create a cursor object; basically an iterator for select queries.
curs 	= db.cursor()

#selects timestamp, tg_id, direction...etc from previous hour (first 1000 results ordered by total HPL calls) for OLD TABLE.
"""
curs.execute('SELECT tstamp, tg_id, direction, attempts, answered, failed, otg_hlpkt_calls, dtg_hlpkt_calls, (otg_hlpkt_calls+dtg_hlpkt_calls) AS total_hlpkt_calls \
				FROM ossdb.cs_tg_hour \
				WHERE tstamp > SYSDATE - (2/24) \
				AND tstamp < SYSDATE - (1/24) \
				ORDER BY total_hlpkt_calls DESC')
#NOTE: for SYSDATE - (2/24) to SYSDATE - (1/24), I think this should hit the 2nd to last hour properly
#E.G: If current time is 12:15, should look at hour 10-11.
"""

print(datetime.now())
curs.execute('SELECT * FROM ossdb.v_tg_pkt_loss ORDER BY tstamp DESC')

print_fields(curs)
print_hpl_rows(curs)
check_pktloss(curs)

db.close()
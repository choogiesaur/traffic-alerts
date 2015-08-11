import cx_Oracle
from dbtest import get_sysdate
from datetime import date, datetime, timedelta

#info for our db
host 	= 'ex01-scan.prod.idt.net'
port 	= 1521
service = 'ossdb.db.idt.net'

#connecting to cdrcsa database via service name
dsn_tns = cx_Oracle.makedsn(host, port, service_name=service)
db 		= cx_Oracle.connect('OSSREAD', 'oss2002read', dsn_tns)

#create a cursor object; basically an iterator for select queries.
curs 	= db.cursor()

curs.execute('SELECT SYSDATE FROM ossdb.v_tg_pkt_loss WHERE rownum <= 1')

sysdate = datetime.now();
print(sysdate)

shiftdate = sysdate + timedelta(hours=4)
print(shiftdate)

tempdate = shiftdate + timedelta(hours=-2)
print(tempdate)

hms = timedelta(hours=20,minutes=11,seconds=13)
print(hms)

resolution=timedelta(seconds=10)

print(timedelta(seconds=hms.seconds%resolution.seconds))

resolution = timedelta(hours=1)
print(timedelta(seconds=hms.seconds%resolution.seconds))
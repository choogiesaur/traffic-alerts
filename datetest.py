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

gmt_m2 = sysdate + timedelta(hours=2)
print(gmt_m2)

floored = gmt_m2.replace(minute=0,second=0,microsecond=0)
print(floored)


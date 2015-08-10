import cx_Oracle

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

for row in curs:
	print(str(row[0]))
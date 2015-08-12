# smtplib module send mail

import smtplib
import socket

recipients = ['firas.sattar@idt.net', 'traffic.summarizer.alerts@gmail.com']
TO 		= 'firas.sattar@idt.net'
SUBJECT = 'TEST MAIL no ttls'
TEXT 	= 'Here is a message from python.'

# Gmail Sign In
gmail_sender = 'traffic.summarizer.alerts@gmail.com'
gmail_passwd = 'idtengineering123!'

server = smtplib.SMTP_SSL('smtp.gmail.com:465')
server.ehlo()
server.login(gmail_sender, gmail_passwd)

BODY = '\r\n'.join(['To: %s' % TO,
                    'From: %s' % gmail_sender,
                    'Subject: %s' % SUBJECT,
                    '', TEXT])

try:
    server.sendmail(gmail_sender, [TO], BODY)
    print ('email sent')
except:
    print ('error sending mail')

server.quit()
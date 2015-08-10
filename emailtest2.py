import smtplib

sender = 'choogiesaur@gmail.com'
receivers = ['firas.sattar@idt.net']

message = """From: From Person <from@fromdomain.com>
To: To Person <to@todomain.com>
Subject: SMTP e-mail test

This is a test e-mail message dawg.
"""

try:
   smtpObj = smtplib.SMTP('localhost')
   smtpObj.sendmail(sender, receivers, message)         
   print ("Successfully sent email")
except Exception:
   print ("Error: unable to send email")
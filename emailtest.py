import smtplib
import socket

s = smtplib.SMTP("smtp.gmail.com",587)
s.starttls()
#s.ehlo
try:
    s.login('choogiemaple@gmail.com', 'choogiemaple64')
except SMTPAuthenticationError:
    print('SMTPAuthenticationError')
s.sendmail('choogiemaple@gmail.com', 'choogiemaple@gmail.com', 'no ehlo lol')
s.quit()
# traffic-alerts

**Dependencies:** ***Python3***, ***cx_Oracle***, ***HTML.py***

Tool I built during an internship for periodically scanning telecom network traffic and generating alerts based on certain conditions. A crontabbed shell script on a dev server will run **traffic-alerts.py** every hour. For each alert, this tool: 

- queries the specific database view pertaining to metrics for the given alert (packet loss, route advanceable response, call duration)
- calls alert function to scan the result set for given conditions
- calls html generation function to create the alert message and html table
- sends email to list of recipients via google SMTP.

**Currently implemented alerts:**
- If high packet loss (>1%) on a certain hour is greater than 15% of all Completed Calls on that hour, then send email alert. Number of completed calls > 1000.
- Alert for any outbound carriers who on average take greater than 6 seconds to signal a route advance-able sip response. Minimal route advanceable call must be greater than 100. Number of Route-advanceable calls must be greater than 20% of attempts.
- If Duration is less than 30 sec for greater than 80% of completed calls, then alert. Or Duration is less than 60 sec for greater than 95% of completed calls, then alert. Minimum 1000 call answered.

**TODO:** 
- Switch to local SMTP/incorporate mailx

**Usage:**
> python traffic-alerts.py
> ( but really you want this as a recurring job :) )

**Notes:**
- Meant for python 3, but runs on python 2.6 with \__future\__ import
- When implementing new alerts, the function print_fields() in deprecated.py is useful for lining up database fields with the python program.
- More notes in notes.txt :)

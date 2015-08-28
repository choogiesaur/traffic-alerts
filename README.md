# traffic-alerts

**Dependencies:** ***Python3***, ***cx_Oracle***, ***HTML.py***

Tool for periodically scanning network traffic and generating alerts based on certain conditions. chrontab'd shell script on vetools that runs dbtest.py every hour. for each alert, this tool: 

- queries the specific database view for the given alert
- calls alert function to scan the result set for given conditions
- calls html generation function to create the alert message and html table
- sends email to list of recipients via google SMTP.

**TODO:** 
- Switch to local SMTP/incorporate mailx
- If possible, instead of using list-of-lists for offenders, have a row object with named attributes for each database field. Higher space requirement, but much greater ease of use.

**Currently implemented alerts:**
- If high packet loss (>1%) on a certain hour is greater than 15% of all Completed Calls on that hour, then send email alert. Number of completed calls > 1000.
- Alert for any outbound carriers who on average take greater than 6 seconds to signal a route advance-able sip response. Minimal route advanceable call must be greater than 100. Number of Route-advanceable calls must be greater than 20% of attempts.
- If Duration is less than 30 sec for greater than 80% of completed calls, then alert. Or Duration is less than 60 sec for greater than 95% of completed calls, then alert. Minimum 1000 call answered.

**Usage:**
> python dbtest.py

**Notes:**
- Some of the formatting looks clean in a text editor but a bit iffy on GitHub.
- Meant for python 3, but is able to run on vetools' python 2.6 with \__future\__ import
- When implementing new alerts, the function print_fields() in deprecated_fxns.py is useful for lining up database fields with the python program.

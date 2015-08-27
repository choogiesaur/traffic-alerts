# traffic-alerts
Tool for periodically scanning network traffic and generating alerts based on certain conditions.

Dependencies: **Python3**, **cx_Oracle**, **HTML.py**

Currently implemented alerts:
- If high packet loss (>1%) on a certain hour is greater than 15% of all Completed Calls on that hour, then send email alert. Number of completed calls > 1000.
- Alert for any outbound carriers who on average take greater than 6 seconds to signal a route advance-able sip response. Minimal route advanceable call must be greater than 100. Number of Route-advanceable calls must be greater than 20% of attempts.

Usage: 
> python dbtest.py

Notes: 
- Some of the formatting looks clean in a text editor but a bit iffy on GitHub.
- Meant for python 3, but is able to run on vetools' python 2.6 with \__future\__ import

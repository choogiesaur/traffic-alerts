# traffic-alerts
Tool for periodically scanning network traffic and generating alerts based on certain conditions.
Currently implemented alerts:
- If high packet loss (>1%) on a certain hour is greater than 15% of all Completed Calls on that hour, then send email alert to FaultDesk and Engineering. Number of completed calls > 1000.


Dependencies: **Python3**, **cx_Oracle**

Usage: 
> python dbtest.py

Notes: 
- Some of the formatting looks clean in a text editor but a bit iffy on GitHub.
- Meant for python 3, but is able to run on vetools' python 2.6 with __future__ import

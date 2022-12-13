#### Daniels CP API Cleanup SCript ####

13/12/22 - DPC

I wrote this to run the "show-unused-objects" command on a Check Point management server, due to limitations inside the
console of only 500 objects. It runs the command though the web API (after logging in with your admin credentials) 
pulls all the objects in loops, sorts and then sends back the relevant delete commands (along with scheduled publishes)
to delete them.

You need to amend the following values;

MDSCMAIP - _this is the IP of your management/domain server_

uservar - _your username_

passvar - _your password_

This is a work in progress, but is fully functional and tested on R80.40/R81.10 - it doesn't delete unused VPN Communities
this was semi-intentional, as they are generally more sensitive objects. You can however add the URL to the "data-urls"
and an extra command to the main loop to achieve this, should you wish.

I plan to add more detail to this, by getting unique values from the pulled dictionaries and then passing that to a loop
which then deletes them (whereas, at the moment it just tries all options and loops over them a few times).

Make sure the API is open and reachable from where you're running the script. The API on R80.40 was more sensitive, and would
occasionally fall over (you can check it's status with 'api status') but changes are pushed in 200 change blocks (or less)
which mostly mitigate this. 

As everything is done in a session and published separately, you can review the pushed sessions in the history or even restore them.

The script does not self run. It's designed to be run from a python shell, with launching the main loop with;

RunTheCleanUp()

Each session that is created is stored and tracked in the SessionTracker.

There is a dictionary I am working on for bulk-changes included, but this is taken from the main Management API reference
guide;

https://sc1.checkpoint.com/documents/latest/APIs/#introduction~v1.9%20

#!/usr/bin/env python

# Brad Bonn
# IBM Cloud Data Services
# bbonn@us.ibm.com

# This script pulls the list of databases to replicate from a shared Cloudant database
# that's world-readable from this address:
sourceListURL = "https://bradwbonn.cloudant.com/potreplicator/sources"
# Amount of time to monitor for active replications in seconds
timeout = 15 * 60

# If the database names need to change, you can contact Brad to have the doc updated,
# or you can request write access to the database from him to make the changes yourself

# Document format is:
#{
#  "_id": "sources",
#  "PoTs": {
#   "cloudant": [],
#   "dashdb": [
#    "https://redbookid.cloudant.com/retaildemo-visitor",
#    "https://redbookid.cloudant.com/retaildemo-store",
#    "https://redbookid.cloudant.com/retaildemo-dept",
#    "https://redbookid.cloudant.com/retaildemo-desk",
#    "https://redbookid.cloudant.com/retaildemo-slot"
#    ],
#   "watson analytics": [],
#   "BI on Cloud": []
#  }
# }

import requests
import json
import re
import time
import sys

print "This script will import the example databases into your account."
print "In order to use it, please ensure you're connected to the internet."
# Get the user's base64 credentials and validate they work
# CloudantAuth = getCloudantAuth()
cloudant_user = raw_input("Enter your Cloudant account name > ")
cloudant_pass = raw_input("Enter your Cloudant password > ")
usrPass = userid + ":" + password
cloudant_auth = base64.b64encode(usrPass)
test_URI = "https://" + cloudant_user + ".cloudant.com"
# Test auth by opening a cookie session, if not good try again
if (test_auth(test_URI, cloudant_user, cloudant_pass)):
    print "Credentials valid"
else:
    exit()

# Import the set of databases to replicate from the shared database
fullheader = {"Content-Type":"application/json"}
response = requests.get(
    sourceListURL,
    headers = fullheader
)
sourceReference = response.json()
# Obtain the array of databases to replicate from resulting JSON
databaseList = get_db_list(sourceReference)
# Begin replication process
if (start_replication(databaseList, cloudant_user, cloudant_pass)):
    print "Replication process initiated..."
    monitor_replication(databaseList, cloudant_user, cloudant_pass)
else:
    print "ERROR: No replication tasks started."
    print "Please check with your instructor for assistance."
    exit()

# Obtain the user's login credentials for Cloudant (their account for the DBs to be loaded to)
# Keep asking if the credentials turn out invalid
# DEPRECATED
#def getCloudantAuth():
#    auth_not_set = 1
#    while (auth_not_set):
#        cloudant_user = raw_input("Enter your Cloudant account name > ")
#        cloudant_pass = raw_input("Enter your Cloudant password > ")
#        usrPass = userid + ":" + password
#        cloudant_auth = base64.b64encode(usrPass)
#        test_URI = "https://" + cloudant_user + ".cloudant.com"
#        # Test auth by opening a cookie session, if not good try again
#        if (test_auth(test_URI, cloudant_user, cloudant_pass)):
#            auth_not_set = 0
#    return(cloudant_auth)

# Use public sources document in order to get the appropriate list of databases to replicate
# Currently, this just gets all DBs for all PoTs and returns them as an array.
def get_db_list(sourceReference):
    for potname in sourceReference[PoTs]:
        for DBURL in sourceReference[potname]:
            listOfDatabases.append(DBURL)
    return(listOfDatabases)    

# Future expansion: obtain a list of all PoTs from the sources document
def get_pot_list():
    return ()

# Function to monitor status of replication tasks and notify user upon completion
def monitor_replication(databaseList, user, password):
    # For now, check to see if any replications are active. Repeat until they're no longer active.
    # Future expansion: Check for only tasks related to the passed list of databases. (In case the user is doing other replications already)
    tasksURI = "https://" + user + ".cloudant.com/_active_tasks"
    
    # Populate an array with the db names for finding by task _id
    dbarray = []
    for dbURL in databaseList:
        m = re.search('\/(.+?)$', URL)
        if m:
            databasename = m.group(1)
            dbarray.insert(databasename)

    # Loop through testing for replication completion.  Timeout after set value.
    replicationUnderway = TRUE
    startTime = time.time()
    endTime = time.time()
    while (replicationUnderway & ((endTime - startTime) < timeout)):
        # Get active tasks JSON
        response = requests.get(
            tasksURI,
            headers = fullheaders,
            params = {'name': user, 'password': password}
        )
        # Check all results for changes pending
        taskJSON = response.json()
        completeTest = TRUE
        for doc in taskJSON:
            if ((doc.type == "replication") & (doc.changes_pending > 0)):
                completeTest = FALSE
        if completeTest == TRUE:
            replicationUnderway = FALSE
        else:
            # Incomplete. Update timer and error if timeout achieved.
            # Make a spinny visual while waiting to query
            spinny()
            endTime = time.time()
            if ((endTime - startTime) < timeout):
                print "ERROR: Replication has taken longer than 15 minutes."
                print "Check with your instructor for assistance."
    
def spinny():
    print "replicating databases...\\",
    syms = ['\\', '|', '/', '-']
    bs = '\b'
    for _ in range(10):
        for sym in syms:
            sys.stdout.write("\b%s" % sym)
            sys.stdout.flush()
            time.sleep(.5)


# Create a cookie with passed auth parameters, return true and create _replicator database if valid
def test_auth(baseURI, user, password):
    fullURI = baseURI + "/_session"
    fullheaders = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        fullURI,
        headers = fullheaders,
        params = {'name': user, 'password': password}
    )
    if (response.status_code not in (200,201,202)):
        print "Sorry, login credentials invalid, please try again."
        return(False)
    requests.delete(
        fullURI,
        headers = {"Content-Type": requests.cookies['AuthSession']}
    )
    fullURI = baseURI + "/_replicator"
    response = requests.put(
        fullURI,
        headers = fullheaders,
        params = {'name': user, 'password': password}
    )
    if (response.status_code not in (200,201,202)):
        print "Sorry, cannot create _replicator database. Check your login account's permissions. API keys cannot be used."
        return(False)
    return(True)

# Create a replication document JSON using the source URL
def make_replication_doc(URL, username, password):
    m = re.search('\/(.+?)$', URL)
    if m:
        databasename = m.group(1)
    tempdoc = {}
    tempdoc['source'] = URL
    tempdoc['target'] = "https://" + username + ":" + password + "@" + username + ".cloudant.com/" + databasename
    tempdoc['continuous'] = False
    tempdoc['_id'] = databasename
    repJSON = json.dumps(tempdoc)
    return(repJSON)

# Insert a replication document into the _replicator database for each entry in the passed list
def start_replication(databaseList, username, password):
    replicatorURL = "https://" + username + ".cloudant.com/_replicator"
    for databaseURL in databaseList:
        thisJSON = make_replication_doc(databaseURL, username, password)
        response = requests.put(
            replicatorURL,
            headers = fullheaders,
            params = {'name': username, 'password': password},
            data = thisJSON
        )
        if (response.status_code not in (200,201,202)):
            print "Error: Couldn't insert replication document for " + databaseURL
            print response.status_code
        else:
            successStatus = TRUE
    return (successStatus)

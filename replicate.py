#!/usr/bin/env python

# Brad Bonn
# IBM Cloud Data Services
# bbonn@us.ibm.com

# This script pulls the list of databases to replicate from a shared Cloudant database

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

# Configuration values
config = dict(
    timeout = 900,
    mycookie = '',
    authheader = '',
    replicatorURL = '',
    sessionURI = '',
    baseURI = '',
    cloudant_user = '',
    cloudant_pass = '',
    jsonheader = {"Content-Type":"application/json"},
    sourceListURL = "https://bradwbonn.cloudant.com/potreplicator/sources",
    databaselist = []
)

# Use public sources document in order to get the appropriate list of databases to replicate
# Currently, this just gets all DBs for all PoTs and returns them as an array.
def get_db_list(sourceReference):
    for potname in sourceReference['PoTs']:
        if potname > 0:
            for DBURL in sourceReference[potname]:
                listOfDatabases.append(DBURL)
    return(listOfDatabases)

# Future expansion: obtain a list of all PoTs from the sources document
def get_pot_list():
    return ()

# Function to monitor status of replication tasks and notify user upon completion
def monitor_replication(databaseList):
    # For now, check to see if any replications are active. Repeat until they're no longer active.
    # Future expansion: Check for only tasks related to the passed list of databases. (In case the user is doing other replications already)
    tasksURI = config['baseURI'] + "/_active_tasks"
    
    # Populate an array with the db names for finding by task _id
    dbarray = []
    for dbURL in databaseList:
        m = re.search('\/(.+?)$', URL)
        if m:
            databasename = m.group(1)
            dbarray.insert(databasename)

    # Loop through testing for replication completion.  Timeout after set value.
    replicationUnderway = True
    startTime = time.time()
    endTime = time.time()
    while (replicationUnderway & ((endTime - startTime) < timeout)):
        # Get active tasks JSON
        response = requests.get(
            tasksURI,
            headers = config['authheader']
        )
        # Check all results for changes pending
        taskJSON = response.json()
        completeTest = True
        for doc in taskJSON:
            if ((doc.type == "replication") & (doc.changes_pending > 0)):
                completeTest = False
        if completeTest == True:
            replicationUnderway = False
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
def test_auth():
    config['sessionURI'] = config['baseURI'] + "/_session"
    authdata = dict(name=config['cloudant_user'],password=config['cloudant_pass'])
    cookieheader = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': 32,
        'Accept': '*/*'
    }
    response = requests.post(
        config['sessionURI'],
        headers = cookieheader,
        data = authdata
    )
    if (response.status_code not in (200,201,202)):
        print response.status_code
        print response.raise_for_status()
        print "Sorry, login credentials invalid, please try again."
        return(False)
    config['mycookie'] = response.headers['set-cookie']
    config['authheader'] = {"Content-Type":"application/json","Cookie":config['mycookie']}
    # Check to see if replicator exists
    config['replicatorURL'] = config['baseURI'] + "/_replicator"
    response = requests.get(
        config['replicatorURL'],
        headers = config['authheader']
    )
    if (response.status_code == 404):
        response = requests.put(
            config['replicatorURL'],
            headers = config['authheader']
        )
        if (response.status_code not in (200,201,202)):
            print "Sorry, cannot create _replicator database. Check your login account's permissions. API keys cannot be used."
            return(False)
    return(True)

# Create a replication document JSON using the source URL
def make_replication_doc(URL):
    m = re.search('\/(.+?)$', URL)
    if m:
        databasename = m.group(1)
    tempdoc = dict(
        source = URL,
        target = "https://" + config['cloudant_user'] + ":" + config['cloudant_pass'] + "@" + config['cloudant_user'] + ".cloudant.com/" + databasename,
        continuous = False,
        _id = databasename
    )
    repJSON = json.dumps(tempdoc)
    return(repJSON)

# Insert a replication document into the _replicator database for each entry in the passed list
def start_replication(databaseList):
    for databaseURL in databaseList:
        thisJSON = make_replication_doc(databaseURL)
        response = requests.put(
            config['replicatorURL'],
            headers = config['authheader'],
            data = thisJSON
        )
        if (response.status_code not in (200,201,202)):
            print "Error: Couldn't insert replication document for " + databaseURL
            print response.json()
        else:
            successStatus = True
    return (successStatus)

# Main code begins here
print "This script will import the example databases into your account."
print "In order to use it, please ensure you're connected to the internet."
config['cloudant_user'] = raw_input("Enter your Cloudant account name > ")
config['cloudant_pass'] = raw_input("Enter your Cloudant password > ")
config['baseURI'] = "https://" + config['cloudant_user'] + ".cloudant.com"

# Test auth by opening a cookie session, if not good try again
if test_auth():
    print "Credentials valid"
else:
    exit()

# Import the set of databases to replicate from the shared database
response = requests.get(
    config['sourceListURL'],
    headers = config['jsonheader']
)
sourceReference = response.json()
print sourceReference
# Obtain the array of databases to replicate from resulting JSON
config['databaseList'] = get_db_list(sourceReference)

# Begin replication process
if (start_replication(config['databaseList'])):
    print "Replication process initiated..."
    monitor_replication(config['databaseList'])
else:
    print "ERROR: No replication tasks started."
    print "Please check with your instructor for assistance."
    exit()

# Remove cookie when finished
requests.delete(
    config['sessionURI'],
    headers = config['authheader']
)


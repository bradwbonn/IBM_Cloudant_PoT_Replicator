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
    databaselist = [],
    replicationIds = []
)

# Use public sources document in order to get the appropriate list of databases to replicate
# Currently, this just gets all DBs for all PoTs and returns them as an array.
def get_db_list(sourceReference):
    listOfDatabases = []
    for potname in sourceReference['PoTs']:
        if sourceReference['PoTs'][potname] > 0:
            for DBURL in sourceReference['PoTs'][potname]:
                listOfDatabases.append(DBURL)
    return(listOfDatabases)

# Get replicator doc get with auth config
def getRepDoc(docID):
    URI = config['baseURI'] + "/_replicator/" + docID
    response = requests.get(
        URI,
        headers = config['authheader']
    )
    return response.json()

def getActiveTask(repID):
    # Get active tasks JSON
    response = requests.get(
        tasksURI,
        headers = config['authheader']
    )
    if len(response.json()) > 0:
        for task in response.json():
            if task['type'] == 'replication':
                if task['doc_id'] == repID:
                    return task['changes_pending']
                else:
                    next()
            else:
                next()
        return "NOT STARTED"
    else:
        return "NOT STARTED"

# Function to monitor status of replication tasks and notify user upon completion
def monitor_replication(databaseList):
    # For now, check to see if any replications are active. Repeat until they're no longer active.
    # Future expansion: Check for only tasks related to the passed list of databases. (In case the user is doing other replications already)
    tasksURI = config['baseURI'] + "/_active_tasks"
    
    # Populate an array with the db names for finding by task _id
    dbarray = []
    for URL in databaseList:
        m = re.search('.*\/(.+?)$', URL)
        if m:
            databasename = m.group(1)
            dbarray.insert(databasename)

    # Loop through testing for replication completion.  Timeout after set value.
    replicationUnderway = True
    startTime = time.time()
    endTime = time.time()
    notCompleted = True
    while (notCompleted):
        statuses = dict()
        # Loop through all IDs of rep docs created
        for docID in config['replicationIds']:
            # get "_replication_state" for this doc
            # If "triggered":
            if (getRepDoc(docID)['_replication_state'] == "triggered"):
                # Poll _active_tasks for corresponding doc
                taskState = getActiveTask(docID)
                # if doc doesn't exist, or "changes_pending" == "None":
                if (taskState == "NOT STARTED" or taskState == "None"):
                    # put key/value of replication name, "Standby" into statusdict
                    statuses[docID] = "Standby"
                else:
                    # put key/value of replication name, "Running" into statusdict
                    statuses[docID] = "Running"
            else:
                if (getRepDoc(docID)['_replication_state'] == "completed"):
                    # put key/value of replication name, "Complete" into statusdict
                    statuses[docID] = "Complete"
                else:
                    # put key/value of replication name, "Error" into statusdict
                    statuses[docID] = "Error"
        # Print a table of the replication statuses
        notCompleted = False
        print '------------------'
        for key in statuses:
            print('Task: {0} Status: {1}'.format(key,statuses[key]))
            if statuses[key] == "Standby" or statuses[key] == "Running":
                notCompleted = True
            else:
                next()
        print '------------------'
        # Print a dot each second for 10 seconds
        for x in range (1,10):
            print '.'
            time.sleep(1)

    # Sit on active tasks until they are completed
    # CODE BELOW HERE BAD
    #while (replicationUnderway & ((endTime - startTime) < timeout)):
    #    # Get active tasks JSON
    #    response = requests.get(
    #        tasksURI,
    #        headers = config['authheader']
    #    )
    #    # Check all results for changes pending
    #    taskJSON = response.json()
    #    completeTest = True
    #    for doc in taskJSON:
    #        if (doc['type'] == "replication"):
    #            completeTest == False
    #    if completeTest == True:
    #        replicationUnderway = False
    #    else:
    #        # Incomplete. Update timer and error if timeout achieved.
    #        # Make a spinny visual while waiting to query
    #        spinny()
    #        endTime = time.time()
    #        if ((endTime - startTime) < timeout):
    #            print "ERROR: Replication task has taken longer than 15 minutes."
    #            print "Check with your instructor for assistance."
    # CODE ABOVE HERE BAD
    
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
    m = re.search('.*\/(.+?)$', URL)
    if m:
        databasename = m.group(1)

    tempdoc = dict(
        source = URL,
        name = URL,
        target = "https://" + config['cloudant_user'] + ":" + config['cloudant_pass'] + "@" + config['cloudant_user'] + ".cloudant.com/" + databasename,
        continuous = False,
        create_target = True,
    )
    repJSON = json.dumps(tempdoc)
    return(repJSON)

# Insert a replication document into the _replicator database for each entry in the passed list
def start_replication(databaseList):
    successStatus = False
    for databaseURL in databaseList:
        thisJSON = make_replication_doc(databaseURL)
        response = requests.post(
            config['replicatorURL'],
            headers = config['authheader'],
            data = thisJSON
        )
        if (response.status_code not in (200,201,202)):
            print "Error: Couldn't insert replication document for " + databaseURL
            print response.json()
        else:
            successStatus = True
            config['replicationIds'].insert(response.json()['id'])
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


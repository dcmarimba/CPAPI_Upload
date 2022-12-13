import urllib3, json, requests.packages, time

# fixed vars
MDSCMAIP = '192.168.202.100'
HTTPSPORT = '443'
uservar = ''
passvar = ''

# variable vars
requests.urllib3.disable_warnings()
https = urllib3.HTTPSConnectionPool(MDSCMAIP, HTTPSPORT, cert_reqs='CERT_NONE', assert_hostname=False)

# dictionary of keys for API
SessionTracker = {}

logindict = {
    "user": uservar,
    "password": passvar,
    "continue-last-session" : "true"
}

urlkeys = {
    "loginurl" : "/web_api/login",
    "publishurl" : "/web_api/publish",
    "logouturl" : "/web_api/logout",
    "logindomainurl" : "/web_api/login-to-domain",
    "show-task" : "/web_api/show-task/"
}

dataurls = {
    "show-unused-objects" : "/web_api/show-unused-objects",
    "add-host" : "/web_api/add-host",
    "delete-host" : "/web_api/delete-host",
    "delete-network" : "/web_api/delete-network",
    "delete-service-tcp" : "/web_api/delete-service-tcp",
    "delete-service-udp" : "/web_api/delete-service-udp",
    "delete-group" : "/web_api/delete-group",
    "delete-address-range" : "/web_api/delete-address-range",
    "delete-dynamic-object" : "/web_api/delete-dynamic-object",
    "delete-dns-domain" : "/web_api/delete-dns-domain",
    "delete-service-group" : "/web_api/delete-service-group",
    "delete-service-dce-rpc" : "/web_api/delete-service-dce-rpc"
}

functionschemadict = {
    "add-host" : {
        "val1" : "name",
        "val2" : "ip-address"
    },
    "add-network" : {
        "val1" : "name",
        "val2" : "subnet",
        "val3" : "mask-length",
        "val4" : "subnet-mask"
    },
    "delete-host" : {
        "val1" : "name",
        "val2" : "uid"
    },
    "show-unused-objects" : {
        "val1" : "limit",
        "val2" : "offset",
        "val3" : "details-level"
    },
    "delete-network" : {
        "val1" : "name",
        "val2" : "uid"
    },
    "delete-service-tcp" : {
        "val1" : "name",
        "val2" : "uid"
    },
    "delete-service-udp" : {
        "val1" : "name",
        "val2" : "uid"
    },
    "delete-group" : {
        "val1" : "name",
        "val2" : "uid"
    },
    "delete-address-range" : {
        "val1" : "name",
        "val2" : "uid"
    }
}

functiondict = {
    "show-unused-objects" : {
        "limit" : "50",
        "offset" : "0",
        "details-level" : "full"
    }
}

def GetTime(sessionlength, function):
    from datetime import datetime, timedelta
    datetimenow = datetime.now()
    timeformat = '%d/%m/%Y, %H:%M:%S'
    curtime = datetimenow
    curtimeformatted = curtime.strftime(timeformat)
    plustime = datetimenow + timedelta(seconds=(sessionlength))
    plustimeformatted = plustime.strftime(timeformat)
    if function == 'now':
        return curtimeformatted
    elif function == 'expiry':
        return plustimeformatted

def APILoginv2(SeshName):
    global SessionTracker
    allheaders = {'Content-Type': 'application/json'}
    logindict['session-name'] = SeshName
    LoginBody = json.dumps(logindict)
    postrequest = https.request('POST', str(urlkeys.get('loginurl')), headers=allheaders, body=LoginBody)
    if postrequest.status == 200:
        step1 = json.loads(postrequest.data)
        sid = step1.get('sid')
        uid = step1.get('uid')
        timeout = step1.get('session-timeout')
        if sid not in SessionTracker:
            TimeNow = GetTime(timeout, 'now')
            TimeExp = GetTime(timeout, 'expiry')
            step1a = SessionTracker[str(sid)] = {'UID': str(uid), 'SID': str(sid), 'LoginTime': str(TimeNow), 'DefaultSessionExpiry': str(TimeExp), 'Session Time-Out': int(timeout), 'Session Name': str(SeshName)}
        return sid

def APIPublish(sid):
    global SessionTracker
    PubInProgress = 0
    PubHeaders = {'Content-Type': 'application/json'}
    PubHeaders.update({'X-chkp-sid': str(sid)})
    PublishBody = '{ }'
    postrequest = https.request('POST', str(urlkeys.get('publishurl')), headers=PubHeaders, body=PublishBody)
    if postrequest.status != 200:
        PubInProgress = 1
        step1 = json.loads(postrequest.data)
        step2 = step1.get('task-id')
        step3 = GetTime(600, 'now')
        sidentry = SessionTracker[str(sid)]
        sidentry['Published Task ID'] = step2
        sidentry['Publish Time'] = step3
        while PubInProgress == 1:
            print('Publish in progress of session..', sid)
            taskbody = {'task-id': str(step2)}
            taskbodyload = json.dumps(taskbody)
            task = https.request('POST', str(urlkeys.get('show-task')), headers=PubHeaders, body=taskbodyload)
            step1a = json.loads(task.data)
            print('Current task status is..', step1a.get('status'))
            if step1a.get('status') == 'succeeded':
                print('Publish success, SID', step2)
                PubInProgress = 0
                return True
            elif step1a.get('status') != 'succeeded':
                sleeptime = 10
                print('Current task status is..', step1a.get('status'))
                print('Sleeping for ', sleeptime)
                time.sleep(sleeptime)
                continue
    elif postrequest.status == 200:
        step1 = json.loads(postrequest.data)
        step2 = step1.get('task-id')
        step3 = GetTime(600, 'now')
        sidentry = SessionTracker[str(sid)]
        sidentry['Published Task ID'] = step2
        sidentry['Publish Time'] = step3
        TimeNow = GetTime(600, 'now')
        print('Publish success, SID', step2, TimeNow)
        return True

def GetNewVals(operation, CurSid):
    allheaders = {'Content-Type': 'application/json'}
    if CurSid != '':
        workingdictlist = []
        allheaders.update({'X-chkp-sid': str(CurSid)})
        initialbody = json.dumps({'limit': '0', 'offset': '0'})
        step1 = https.request('POST', str(dataurls.get(operation)), headers=allheaders, body=initialbody)
        step2 = json.loads(step1.data)
        step3 = step2.get('total')
        step4 = range(0, step3, 50)
        print('Total (current) Unusued Objects..', step3)
        for numbers in step4:
            print('Working on set..', numbers)
            functiondict['show-unused-objects']['offset'] = str(numbers)
            loopbody = json.dumps(functiondict.get(operation))
            step1a = https.request('POST', str(dataurls.get(operation)), headers=allheaders, body=loopbody)
            step2a = workingdictlist.append(json.loads(step1a.data))
        print('Grab done!')
        return workingdictlist

def DeleteObjects(deletedict, action, operation, sid):
    ObjectCount = 0
    WorkToBeDone = False
    allheaders = {'Content-Type': 'application/json'}
    allheaders.update({'X-chkp-sid': str(sid)})
    for dict in deletedict:
        for key, value in dict.items():
            if key == 'objects':
                for thing in value:
                    if thing.get('type') == str(action):
                        WorkToBeDone = True
                        ObjectCount = ObjectCount + 1
                        for key, value in thing.items():
                            makebody = json.dumps({'uid': (str(thing.get('uid')))})
                            step1 = https.request('POST', str(dataurls.get(str(operation))), headers=allheaders, body=makebody)
                            if step1.status == 200:
                                print('Deleting Object number..', str(ObjectCount))
                                print('Object Type', action, 'object name', str(thing.get("name")))
                                print('POST Success!')
                                if int(ObjectCount) >= 200:
                                    print('200 Object limit, publishing current changes.')
                                    APIPublish(sid)
                                    ObjectCount = 0
                                    continue
                                continue
    if WorkToBeDone is True:
        APIPublish(sid)
        print('Publishing', str(ObjectCount), 'changes')
    elif WorkToBeDone is False:
        print('Nothing to do for object type', action, 'exit.')

def GetTotals(listdict):
    for dict in listdict:
        if dict['total']:
            return str(dict['total'])

def RunTheCleanUp(loops):
    OutPutVals = {}
    HowManyLoops = loops + 1
    for i in range(0,int(HowManyLoops)):
        print('Connecting to..', str(MDSCMAIP), 'and port..', str(HTTPSPORT))
        CurSID = APILoginv2('DPC Cleanup Script')
        OutPutVals = GetNewVals('show-unused-objects', CurSID)
        Total = GetTotals(OutPutVals)
        print('Total number of objects found..', str(Total))
        DeleteObjects(OutPutVals, 'host', 'delete-host', CurSID)
        DeleteObjects(OutPutVals, 'network', 'delete-network', CurSID)
        DeleteObjects(OutPutVals, 'service-tcp', 'delete-service-tcp', CurSID)
        DeleteObjects(OutPutVals, 'service-udp', 'delete-service-udp', CurSID)
        DeleteObjects(OutPutVals, 'group', 'delete-group', CurSID)
        DeleteObjects(OutPutVals, 'address-range', 'delete-address-range', CurSID)
        DeleteObjects(OutPutVals, 'dynamic-object', 'delete-dynamic-object', CurSID)
        DeleteObjects(OutPutVals, 'dns-domain', 'delete-dns-domain', CurSID)
        DeleteObjects(OutPutVals, 'service-group', 'delete-service-group', CurSID)
        DeleteObjects(OutPutVals, 'service-dce-rpc', 'delete-service-dce-rpc', CurSID)
        print('Done loop', str(i), 'out of', str(HowManyLoops - 1))

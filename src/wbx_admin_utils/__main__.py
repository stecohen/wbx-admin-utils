#!/usr/local/bin/python3

import csv
import requests
import os
import json
import logging
import time
import argparse
import re      
import datetime
import io    
import importlib.metadata
import inspect
import pandas as pd # pd.set_option('display.max_colwidth', None)
import shutil



__version__ = my_name = "N/A"
try:
    __version__ = importlib.metadata.version(__package__)
    my_name = __package__
except:
    print("Local run")

logging.basicConfig()

parser = argparse.ArgumentParser(prog=my_name, description=f"CLI for Webex Admins and Compliance Officers. Version {__version__}")
token=""
if ( 'AUTH_BEARER' in os.environ ):
    token = os.environ['AUTH_BEARER']

parser.add_argument("-t", "--token", dest="token", default=token, help="Access token")
parser.add_argument("-d", "--debug", dest="debug", default=2, help="debug level: 1=errors, 2=success/info, 3=verbose/debug")   
parser.add_argument("-c", "--csvdest", dest="csvdest", default="", help="csv destination file")   
parser.add_argument("-T", "--title", dest="title", action="store_true", help="Add names/title on top of ids (when applicable). This option requires added processing.")   
parser.add_argument('command', type=str, help='enter [%(prog)s help command] to list available commands')    
parser.add_argument('subcommand', type=str, help='')    
parser.add_argument('parameters', type=str, nargs='*', help='')    

args = parser.parse_args()

# Traces 
#
DEBUG=int(args.debug)
if (DEBUG>=3):
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)

NOW = datetime.datetime.now()
UTCNOW = NOW.isoformat() + 'Z'

###################
### UTILS functions 
###################

def trace(lev, msg):
    caller = inspect.stack()[1][3]
    if (DEBUG >= lev ):
        print(f"{caller}: {msg}")

def is_email_format(id):
    trace (3, f"for {id}")  
    m = re.search(".+@.+[.].+$", id)
    if (m) :
        return (True)
    else:
        return(False)

#sets the header to be used for authentication and data format to be sent.
def setHeaders():         
    accessToken_hdr = 'Bearer ' + args.token
    spark_header = {'Authorization': accessToken_hdr, 'Content-Type': 'application/json; charset=utf-8'}
    return (spark_header)

# print items array fields listed in 'il' 
#
def print_items(il, items):
    for i in il:
        print(i,",", end='', sep='')
    print ("")        
    for item in items:
        for i in il:
            try:
                v=item[i]
            except KeyError:
                v=""
            print (v, ",", end='', sep='')
        print ("")

# returms user details in json for given user id
# returns "" if not found or some error   
#
def get_user_details(email_or_uid): 

    trace (3, f"processing user {email_or_uid}")  

    if ( is_email_format(email_or_uid)):
        uid = get_user_id(email_or_uid)
        if (uid=="") :
            return ""
    else:
        uid=email_or_uid

    url=f"https://webexapis.com/v1/people/{uid}"
    r = requests.request("GET", url, headers=setHeaders())
    s = r.status_code
    if s == 200 :
        trace(3,f"found {uid}")
        return(r.json())
    else:
        trace(1,f"did not find {uid}")
        return("")

# generic get data 
# returns {} if not happy  
#
def get_wbx_data(ep, params="", ignore_error=False):
    url = "https://webexapis.com/v1/" + ep + params
    trace(3, f"{url} ")
    try:
        r = requests.get(url, headers=setHeaders())
        s = r.status_code
        if (s == 200):
            d = r.json()
            trace(3, f"success")  
            return(d)
        else:
            not ignore_error and trace(1,f"error {url} {s}: {r.reason}")  
            return({})
    except requests.exceptions.RequestException as e:
        trace(1, f"error {e}")

# returms user id of given user email address 
# returns "" if not found or some error   
#
def get_user_id(ue, ignore_error=False):
    header=setHeaders()
    # disable warnings about using certificate verification
    requests.packages.urllib3.disable_warnings()
    # get_user_url=urllib.parse.quote("https://webexapis.com/v1/people?email=" + ue)
    get_user_url="https://webexapis.com/v1/people?email=" +ue

    trace (3, f"calling {get_user_url}")  
    # send GET request and do not verify SSL certificate for simplicity of this example
    r = requests.get(get_user_url, headers=header, verify=True)
    s = r.status_code
    if s == 200 :
        j = r.json()
        if ( len(j["items"]) == 0 ):
            not ignore_error and trace (1, f"user email {ue} not found")
            return("")
        else:
            if ( len(j["items"]) > 1 ):
                trace(1, f"Error found more than one match for user {ue}")
                return(-2)
            if ( len(j["items"]) == 1 ):
                u = j["items"][0]
                trace (3,f"email {ue} found {u['id']} ")
                return(u['id'])     
    elif s == 404:
        not ignore_error and trace(1,f"got error {s}: {r.reason}")  
        return("")
    else :
        trace(1,f"got error {s}: {r.reason}")  
        return("")
    
# calls given fct for each user in given csv file 
# csv file name  is pointed by the 'index' parameter in the passed array 'a'
# the called fucnt parameters are passed via an array containing the rest of the input array a + email inserted
# exits on file error 
#
def user_csv_command(fct, a, index=0):

    trace (3,f"in user_csv_command {fct.__name__} {a} {index}")
    file=a.pop(index)

    header=setHeaders()
    # disable warnings about using certificate verification
    requests.packages.urllib3.disable_warnings()
    
    try:
        csvfile = open(file)
        trace(3,f"{file} open OK")
    except OSError:
        print (f"Could not open file {file}")
        exit()

    with csvfile:
        reader = csv.DictReader(csvfile)
        found_email_col=False
        for row in reader:
            for em in ['email', 'Email', 'EMAIL']:
                if em in row:
                    found_email_col=True
                    ue=row[em]
                    # call provided function with email inserted 
                    a2=a.copy()
                    a2.insert(index + 1, ue)
                    trace(3,f"calling fct with {a2}")
                    r=fct(a2)
                    if (r>0):
                        trace(3,f"{fct.__name__} command successful for user {ue}") 
                    else:
                        trace(1,f"{fct.__name__} command failed for user {ue}")
                    time.sleep(0.01)
            if not found_email_col :
                print (f"Cannot find 'email' column in {file}.\nCheck format, special characters ect.")
                exit()
            
###################
### GROUPS commands 
###################

# lists all groups 
#
def get_grps_list(a):
    #
    url=f"https://webexapis.com/v1/groups"
    r = requests.request("GET", url, headers=setHeaders())
    s = r.status_code
    j = r.json()
    if s == 200 :
        # print(j)
        hl =[ 'id', 'displayName' ]
        print_items ( hl, j["groups"] )
    else:
        print (f"got error {s}: {r.reason}")  

# lists users in given group id 
# Max 500 : paging not done
#
def list_users_in_grp(a):
    gid=a[0]
    url=f"https://webexapis.com/v1/groups/{gid}/Members?startIndex=1&count=500"
    r = requests.request("GET", url, headers=setHeaders())
    s = r.status_code
    j = r.json()
    if s == 200 :
        print(j)
        hl =[ 'id', 'displayName' ]
        print_items ( hl, j["members"] )
    else:
        trace(1,f"got error {s}: {r.reason}")  


# Adds/Del user id to given group id 
# returns 1 on success 
#
def uid_to_grp(cmd, uid,gid):

    trace (3, f"params : {cmd}, {uid} , {gid} ")
    header=setHeaders()
    # disable warnings about using certificate verification
    requests.packages.urllib3.disable_warnings()

    url=f"https://webexapis.com/v1/groups/{gid}"
    match cmd:
        case "add":
            body='{"members": [ { "id": "' + uid + '" } ] }'
        case "del":
            body='{"members": [ { "id": "' + uid + '" ,"operation":"delete" } ] }'
        case _:
            trace(1,f"invalid command {cmd}")
            return(-1)

    r = requests.patch(url, headers=header, data=body, verify=True)
    s = r.status_code
    if s == 200 :
        trace(3,f"success")  
        return(1) 
    else:
        print (f"got error {s}: {r.reason}")
        return(-1)
    
# Adds/Del user email to given group id 
# returns 1 on success, 0 no action, -1 error 
#
def user_to_grp(a):
    (cmd, ue, gid)=(a[0],a[1],a[2])
    
    trace(3,f"user_to_grp: params = {a}") 

    uid = get_user_id(ue)
    trace(3,f"user_to_grp: got uid = {uid} for email {ue}") 

    if (uid):
        trace(3,f"user_to_grp: calling uid_to_grp for uid {uid}") 
        r=uid_to_grp(cmd, uid, gid)
        if (r > 0):
            trace(2,f"user_to_grp: {cmd} command successful for user {ue}") 
        else:
            trace(1,f"user_to_grp: {cmd} command failed for user {ue}") 
        return(r)
    else:
        trace(1,f"Failed to find user email {ue}") 
        return(0)
    
def add_user_to_grp(a):
    a.insert(0,"add")
    user_to_grp(a)

def del_user_to_grp(a):
    a.insert(0,"del")
    user_to_grp(a)

def add_users_in_csv_to_grp(a):
    a.insert(1,"add")
    user_csv_command(user_to_grp, a)

def del_users_in_csv_to_grp(a):
    a.insert(1,"del")
    user_csv_command(user_to_grp, a)

def uf_add_user_to_grp(a):
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(add_user_to_grp, a)
    else:
        add_user_to_grp(a)

def uf_del_user_to_grp(a):
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(del_user_to_grp, a)
    else:
        del_user_to_grp(a)  

###################
### VM  commands 
###################

# returns json body with VM settings for given user email
# returns -1 on failure 
#
def get_user_vm(a):
    (ue)=(a[0])
    trace(3,f"{a}")
    uid=get_user_id(ue)
    trace(3,f"got id {uid}")

    if (uid):
        header=setHeaders()
        # disable warnings about using certificate verification
        requests.packages.urllib3.disable_warnings()

        url=f"https://webexapis.com/v1/people/{uid}/features/voicemail"
        r = requests.get(url, headers=header, verify=True)
        s = r.status_code
        if s == 200 :
            d = r.json()
            j=json.dumps(d)
            trace(3, f"success {ue} : got {j}")  
            return(j)
        else:
            trace(1, f"got error {s}: {r.reason}")  


# Enables VM for given user email with given json body
# returns 1 on success, negative value on failure 
#
def set_user_vm(a):
    (ue)=(a[0])
    (body)=(a[1])

    trace(3,f"{a}")

    uid=get_user_id(ue)
    if (uid):
        header=setHeaders()
        # disable warnings about using certificate verification
        requests.packages.urllib3.disable_warnings()

        url=f"https://webexapis.com/v1/people/{uid}/features/voicemail"
        r = requests.put(url, headers=header, data=body, verify=True)
        s = r.status_code
        if s == 204 :
            trace(3, f"success")  
            return(1) 
        else:
            trace(1, f"got error {s}: {r.reason}")
            return(-1)
    else:
        trace(1,f"{ue} error ") 
        return(-2)

# Enables VM for given user email based on another user email 'template'
# returns set_user_vm status or -1 if base user not found
#
def set_user_vm_based_on_other_user(a):
    (ue, be)=(a[0], a[1])

    trace(3,f"{a}")

    tmpl=get_user_vm([be])
    if ( tmpl ):
        # replace other email with target email
        bdy=tmpl.replace(be, ue)
        a=[ue,bdy]
        return (set_user_vm(a))
    else:
        trace(1, "error no tmpl")
        return(-1)

def add_vm(a): 
    set_user_vm_based_on_other_user(a)

def uf_add_vm_csv(a): 
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(add_vm, a)
    else:
        add_vm(a)


###############
## USERS DELETE
################

# delete user from given email adress
# returns 1 if good   
#
def del_user(a): 
    ue=a[0]
    trace(3,f"params : {a}")

    uid=get_user_id(ue)
    if (uid): 
        url=f"https://webexapis.com/v1/people/{uid}"
        r = requests.request("DELETE", url, headers=setHeaders())
        s = r.status_code
        if s == 204 :
            trace (2, f"User {ue} deleted ")
            return(1)
        else:
            trace(1,f"Error {s}")  
            trace(1,r.text.encode('utf8'))
            return(-1)
    else:
        trace (1, f"{ue} not found")  
        return(-1)
    
def uf_del_user(a):
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(del_user,a)
    else:
        del_user(a)
    
###############
## USER (DE)ACTIVATION 
################

# activate or deactivate user from given email 
# returns 1 if good   
#
def set_user_active(a): 
    activate=a[0] # boolean 
    ue=a[1]
    trace(3,f"{a}")
    user_json=get_user_details(ue)
    if (user_json):
        uid=user_json['id']
        url=f"https://webexapis.com/v1/people/{uid}"
        r = requests.request("GET", url, headers=setHeaders())
        if ( activate ):
            user_json['loginEnabled']=True
        else:
            user_json['loginEnabled']=False
        trace(3, f"found user {ue} : sending {user_json}") 
        b=json.dumps(user_json)
        r = requests.put(url, headers=setHeaders(), data=b, verify=True)
        s = r.status_code
        if s in (200,204) :
            trace(2, f"user {ue}: active status set to {user_json['loginEnabled']} successfully ")     
            return(1)
        else:
            trace(1,f"actvivate/deactivate_user : Error {s}")  
            trace(1,r.text.encode('utf8'))
            return(-1)
    else:
        trace(1,f"deactivate_user Error ")  
        return(-1)

# 
def uf_activate_user(a):
    match a[0]:
        case 'Yes' | 'yes':
            a[0]=True
        case 'No' | 'no':
            a[0]=False
        case _:
            trace(1,f"Expecting 'Yes' to activate or 'No' to deactivate") 
            return(-1)
    m = re.search(".*[.]csv$", a[1])
    if (m):
        user_csv_command(set_user_active,a,1)
    else:
        set_user_active(a)

###############
## USERS ACCESS TOKEN
################


# delete given user auth id
# returns 1 if good, -1 error
#
def del_user_auth(aid): 
    trace(3,f"in del_user_auth {aid}")

    url=f"https://webexapis.com/v1/authorizations/{aid}"
    r = requests.request("DELETE", url, headers=setHeaders())
    s = r.status_code
    if s == 204 :
        trace (2, f"Auth {aid} deleted")
        return(1)
    else :
        trace(1,f"Error {s}")  
        trace(1,r.text.encode('utf8'))
        return(-1)

# cmd "list" : prints auths for user email
# cmd "get" : returns items obj as per wbx API 
# retuuns 1 if happy 
#
def user_auths(cmd, a): 
    ue=a[0]
    trace(3,f"{ue}")
    uid=get_user_id(ue)
    if (uid):
        url=f"https://webexapis.com/v1/authorizations?personId={uid}"
        r = requests.request("GET", url, headers=setHeaders())
        s = r.status_code
        if s == 200 :
            trace (2, f"auths for user {ue} ID {uid} : ")
            d = r.json()
            items=d['items']
            # print(items)
            for item in items:
                aid=item['id'] 
                match cmd:
                    case "list":
                        print (f"user: {ue}, Application: {item['applicationName']}, Auth: {aid} ")
                        return(1)
                    case "get":
                        trace(2, f"Auth {aid} Application {item['applicationName']}")
                        return(items)
                    case "del":
                        return(del_user_auth(aid))
                    case _:
                        trace(1,f"invalid command {cmd}")
                        return(-1)    
            return(1)   
        else:
            trace(1,f"Error {s}")  
            trace(1,r.text.encode('utf8'))
            return(-1)
    else:
        trace (1, f"{ue} not found")  
        return(-1)

def uf_get_user_details(a):
    j=get_user_details(a[0])
    if (j):
        print (j)
    else:
        print ("That did not work")
    

# delete all access for user email passed as array 
# (not user facing )
#
def del_all_user_auths(a):
    return(user_auths("del", a))

def uf_list_user_auths(a):
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(uf_list_user_auths, a, 0)
    else:
        return(user_auths("list", a))
    

# reset all access for user email passed as array 
# ( user facing )
def uf_del_user_auths(a):
    m = re.search(".*[.]csv$", a[0])
    if (m):
        user_csv_command(del_all_user_auths, a)
    else:
        user_auths("del", a) 

###############
## Comp Officer stuff 
################

# generic head request  
# 
def req_head(url):
    trace(3, f"{url} ")
    try:
        r = requests.head(url, headers=setHeaders())
        s = r.status_code
        if (s == 200):
            d = r.headers
            trace(3, f"success")  
            return(d)
        else:
            trace(1,f"error {s}: {r.reason}")
            return({})
    except requests.exceptions.RequestException as e:
        trace(1, f"error {e}")
        return({})

# generic events API 
# 
def get_events(opts):
    url=f"https://webexapis.com/v1/events{opts}"
    trace(3, f"{url} ")
    try:
        r = requests.get(url, headers=setHeaders())
        s = r.status_code
        if (s == 200):
            d = r.json()
            trace(3, f"success")  
            return(d)
        else:
            trace(1,f"error {s}: {r.reason}")  
    except requests.exceptions.RequestException as e:
        trace(1, f"error {e}")


# extracts file name from content disposition header field 
def extract_file_name(cd):
    name=re.findall('filename="(.+)"', cd)[0]
    return(name)
    
class msgsDF:
    cols = {'id':[],'sentBy':[],'created':[], 'text':[], 'fileCount':[],'files':[], 'fileNames':[], 'roomType':[], 'roomId':[]}
    
    def __init__(self, add_title=False):
        mycols=self.cols
        if  (add_title):
            mycols['title']=[]
        self.df = pd.DataFrame(mycols)
        
    def add_msgs(self, ue, msgs, add_title=False):
        #
        # iterate messages
        for item in msgs['items']:
            msg=item['data']
            title="N/A"
            trace (3, f"got message: " + str(msg))
            #
            # new row from msg
            new_row={}
            for i in self.cols:
                if i in msg:
                    new_row[i]=msg[i]
            #
            # add sender         
            new_row['sentBy']=ue
            #
            # process 'files' column : add 'fileCount' and 'fileNames' values
            file_count=0
            file_list=[]
            if ('files' in msg):
                file_count = len(msg['files'])
                fileURLs=msg['files']
                for furl in fileURLs:
                    trace(3, f"processing {furl}")
                    # read headers
                    hds=req_head(furl)
                    if 'content-disposition' in hds:
                        fn=extract_file_name(hds['content-disposition'])
                        file_list.append(fn)
                    else:
                        trace(3, f"could not find 'content-disposition' header in {furl}")
                new_row['fileNames']=file_list
                trace(3, f"got {new_row['fileNames']}")
            new_row['fileCount'] = int(file_count)
            #
            # add column 'title' if long process option 
            if ( add_title ):
                if 'roomId' in msg:
                    # direct rooms don't have a title. Need to extract the 'other' member in the space
                    if (msg['roomType'] == 'direct'):
                        other_member=get_other_person_membership(msg['roomId'],msg['personId'])
                        # title=f"{other_member['personDisplayName']} ({other_member['personEmail']})"
                        title=f"{other_member['personEmail']}"

                    else:
                        room=get_wbx_data(f"rooms/{msg['roomId']}","")
                        if ('title' in room) :
                            title=room['title']
                    new_row['title']=title
            #
            # finally add to DF  
            if ('created' in msg):
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            #
        return(self.df)
    

# get the 'other' (apart from given 'uid') person membership in a direct 1:1 space
# 
def get_other_person_membership(roomId, uid):
    trace(3, f"{roomId} {uid} ")
    members=get_space_memberships(roomId, True)
    if 'items' in members:
        for item in members['items']:
            if (item['id'] != uid):
                return(item)
    return({})

# get messages obj for given user email 
# optional parameters passed as json string like '{"max":1000}'
# returns empty obj if not found
# 
def get_user_msgs(ue, user_opts=""):

    uid = get_user_id(ue, True)
    frm = datetime.datetime.now() - datetime.timedelta(30)
    utcFrm=frm.isoformat() + 'Z'
    to = UTCNOW
    opts = {'max': 100,'from':utcFrm,'to':to}

    if (uid):
        # override default options w/ user options
        #
        if (user_opts):
            try:
                userOpts=json.loads(user_opts)
                for k in userOpts:
                    opts[k]=userOpts[k]
            except:
                trace(1, f"error parsing {user_opts} not a valid JSON format")

        # construct url parameter string
        #
        params=f"?resource=messages&actorId={uid}"
        for k in opts:
            params=f"{params}&{k}={opts[k]}"
        trace (3, f"params = {params}")
        d=get_events(params)
        return(d)

    else:
        trace(1, f"cannot find user {ue}")
        return({})

# print panda DF from list of messages
# pull msg info in csv fmt  
# 
def print_user_msgs(ue, data):
    # 
    # initialise pandas data frame 
    msgsdf=msgsDF(args.title)
    msgsdf.add_msgs(ue, data, args.title)
    #
    # print to screen and file if option on 
    df = msgsdf.df.astype({'fileCount': 'int'})
    print(df.loc[:, ~df.columns.isin(['id','files', 'roomId'])])
    args.csvdest and df.to_csv(args.csvdest, index=False)

# user facing top level fct 
# get messages for given user email 
# optional parameters passed as json string like '{"max":1000}'
# 
def uf_get_user_msgs(a):
    opts=""
    if len(a) > 1 :
        opts=a[1]
    trace(3, f"got params {a}. Calling get_user_msgs {a[0]} {opts}")
    d=get_user_msgs(a[0], opts)
    if d:
        print_user_msgs(a[0],d)

# list messages sent by each member of given space   
# options 
# 
def uf_get_space_msgs(a):
    #
    # init
    trace(3, str(a))
    rid=a[0]
    if (len(a) > 1 ):
        opts=a[1]
    else:
        opts=""
    msgsdf=msgsDF(False) # msgs DF

    # get list of users in space, extract their msgs, store in panda DF
    #
    members=get_space_memberships(rid)
    if 'items' in members:
        for user in members['items']:
            ue=user['personEmail']
            uid = get_user_id(ue)
            trace(3, f"processing user {ue}")
            if (uid):
                msgs=get_user_msgs(ue, opts)
                trace(3, f"got {str(msgs)[:100]}...")
                msgsdf.add_msgs(ue, msgs, False)
            else:
                trace(3, f"{ue} not found")
        # print
        df=msgsdf.df.sort_values(by=['created'])
        print(df.loc[:, ~df.columns.isin(['id','files', 'roomId'])])
        args.csvdest and df.to_csv(args.csvdest, index=False)
    else:
        trace(3, f"no membership data for {rid}")

# get membership list for given room id  
# 
def get_space_memberships(rid, ignore_error=False):
    url=f"https://webexapis.com/v1/memberships/?roomId={rid}"
    trace(3, f"{url} ")
    try:
        r = requests.get(url, headers=setHeaders())
        s = r.status_code
        if (s == 200):
            d = r.json()
            trace(3, f"success for get_memberships")  
            return(d)
        else:
            not ignore_error and trace(1,f"get_memberships error {s}: {r.reason}")
            trace(3, f"error {s}: {r.reason} ")  
            return({})
    except requests.exceptions.RequestException as e:
        trace(1, f"error {e}")

# pull membership info in csv fmt  
# 
def extract_membership_csv(members):
    #
    cols = {'personEmail':[],'personDisplayName':[],'created':[]}
    df=pd.DataFrame(cols)
    if 'items' in members:
        for mbr in members['items']:
            new_row={}
            for f in cols:
                if f in mbr:
                    new_row[f]=mbr[f]
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        print(df.loc[:, ~df.columns.isin(['id','files', 'roomId'])])
        args.csvdest and df.to_csv(args.csvdest, index=False)
    else:
        trace(3, f"no membership data")  
# user facing top level fct 
# get memberships for given room id 
# 
def uf_get_memberships(a):
    id = a[0]
    data = get_space_memberships(id)
    extract_membership_csv(data)

# download url contents   
# 
def dowmload_contents(url):
    hds=req_head(url)
    if ('Content-Disposition' in hds ):
        cd=hds['Content-Disposition'] 
        trace(3, f"got file {str(hds)}")
        file_name=re.findall('filename="(.+)"', cd)[0]
        """ NOT needed
        ct=hds['Content-Type']
        ctl= ct.split("/") # content type list 
        mode="wb"
        match ctl[0]:
            case "text":
                mode="wb" 
        trace(3,f"got {file_name} {ctl[0]} {mode}")
        """
        try:    
            with requests.get(url, headers=setHeaders()) as r:
                with open(file_name, mode="wb") as f:
                    f.write(r.content)
                    print(f"{file_name} downloaded.")
        except:
            trace(1, f"Error downloading {url}")
    else:
        trace(1, f"no content-disposition in {url}")


def uf_download_msg_attachements(a):
    id = a[0]
    msg = get_wbx_data(f"messages/{id}")
    if 'files' in msg:
        files=msg['files']
        for f in files:
            dowmload_contents(f)
    else:
        trace(1, f"no attachments found in msg {id}")

###############
## syntax
################

def print_help(a): 
    print("Here is some help")

def print_syntax(): 
    for cmd in syntax:
        print(cmd)
        for scmd in syntax[cmd]:
            params=syntax[cmd][scmd]['params']
            hlp=syntax[cmd][scmd]['help']
            prms=""
            for p in params:
                prms=f"{prms} <{p}>"  
            print("   " + scmd + prms + " : " + hlp )
            # print(" " + scmd + ' ' + " ".join(params) + " : " + hlp )

syntax = { 
    "help" : { 
        "commands":              {"params":[],"fct":print_syntax, "help":"display list of available commands"},
    },
    "group" : {
        "list":                 {"params":[],"fct":get_grps_list, "help":"list all groups in admin org"},
        "list-users":           {"params":["group_id"],"fct":list_users_in_grp, "help":"list user ids (max 500) in given group id"},
        "add-user":             {"params":["email|csvFile", "group_id"],"fct":uf_add_user_to_grp, "help":"add user in given group id"},
        "remove-user":          {"params":["email|csvFile", "group_id"],"fct":uf_del_user_to_grp, "help":"remove user from given group id"},
    },
    "user" : {  
        "details":               {"params":["email|user_id"],"fct":uf_get_user_details, "help":"list user details in json"},
        "tokens":                {"params":["email|csvFile"],"fct":uf_list_user_auths, "help":"list user(s) access token"},
        "reset":                 {"params":["email|csvFile"],"fct":uf_del_user_auths, "help":"reset user(s) access token"},
        "activate":              {"params":["Yes|No","email|csvFile"],"fct":uf_activate_user, "help":"activate (Yes) or deactivate (No) user(s)"},
        "delete":                {"params":["email|csvFile"],"fct":uf_del_user, "help":"delete user(s)"},
        "get-vm":                {"params":["email"],"fct":get_user_vm, "help":"dump user voicemail settings in json format"},
        "add-vm":                {"params":["email|csvFile", "base user email"],"fct":add_vm, "help":"set user(s) voicemail options based on another user's voicemail settings "},
    },
    "co" : {
        "list-user-sent-msgs" :  {"params":["email, 'options'"],"fct":uf_get_user_msgs, "help":"list messages sent by a user (last 100 in last 30 days by default) up to 1000 msgs. See expmaples for Options format. -T option applies"}, 
        "list-space-msgs" :      {"params":["roomid, 'options'"],"fct":uf_get_space_msgs, "help":"list messages in a space (last 100 in last 30 days by default) up to 1000 msgs per user. See expmaples for Options format. -T option applies"}, 
        "list-space-members" :   {"params":["id"],"fct":uf_get_memberships, "help":"list members in space "},  
        "get-msg-attachments" :  {"params":["id"],"fct":uf_download_msg_attachements, "help":"download file attachements in message ID"},  
    }          
}


def main():
    # first 2 params are commands
    #
    (cmd1, cmd2) = (args.command, args.subcommand )

    if cmd1 == "help":
        print_syntax()
        exit()

    if cmd1 not in syntax:
        print ("Command [" + cmd1 + "] is invalid")
        print_syntax()
        exit()

    if cmd2 not in syntax[cmd1]:
        print ("Command [" + cmd2 + "] is invalid")
        print_syntax()
        exit()

    # check param count
    #
    par_arr=syntax[cmd1][cmd2]['params']
    if (len(args.parameters) >= len(par_arr)):
        # call function associated with command 
        fct=syntax[cmd1][cmd2]['fct']
        trace(3,f"calling {fct.__name__} with {args.parameters}")
        fct(args.parameters)
    else:
        print("Incorrect parameters. Check syntax ")
        print_syntax()
    #
   
main()
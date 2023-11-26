#!/usr/local/bin/python3

import csv
import requests
import os
import json
import logging
import time
import argparse
import re         

logging.basicConfig()

parser = argparse.ArgumentParser(prog="wbx_admin_utils", description='Various CLI commands for Webex bulk admin talks. ')
token=""
if ( 'AUTH_BEARER' in os.environ ):
    token = os.environ['AUTH_BEARER']

parser.add_argument("-t", "--token", dest="token", default=token, help="Access token")
parser.add_argument("-d", "--debug", dest="debug", default=2, help="debug level: 1=errors, 2=success/info, 3=verbose/debug")   
# parser.add_argument("-s", "--syntax", action='store_true', default=False, help="command list and syntax")   
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


###################
### UTILS functions 
###################


def trace(lev, msg):
    if (DEBUG >= lev ):
        print(msg)

def is_email_format(id):
    trace (3, f"In  is_email_format for {id}")  
    m = re.search(".+@.+\..+$", id)
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

    trace (3, f"In get_user_details for {email_or_uid}")  

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

# returms user id of given user email address 
# returns "" if not found or some error   
#
def get_user_id(ue):
    header=setHeaders()
    
    trace (3, f"In get_user_id for {ue}")  

    # disable warnings about using certificate verification
    requests.packages.urllib3.disable_warnings()
    # get_user_url=urllib.parse.quote("https://webexapis.com/v1/people?email=" + ue)
    get_user_url="https://webexapis.com/v1/people?email=" +ue

    trace (3, f"In get_user_id calling {get_user_url}")  
    # send GET request and do not verify SSL certificate for simplicity of this example
    r = requests.get(get_user_url, headers=header, verify=True)
    s = r.status_code
    if s == 200 :
        j = r.json()
        if ( len(j["items"]) == 0 ):
            trace (0, f"user email {ue} not found")
            return("")
        else:
            if ( len(j["items"]) > 1 ):
                trace(1, f"Error found more than one match for user {ue}")
                return(-2)
            if ( len(j["items"]) == 1 ):
                u = j["items"][0]
                trace (3,f"email {ue} found {u['id']} ")
                return(u['id'])     
    else :
        trace(1,f"get_user_id got error {s}: {r.reason}")  
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
        for row in reader:
            ue=row['email']
            # call provided function with email inserted 
            a2=a.copy()
            a2.insert(index + 1, ue)
            trace(3,f"in user_csv_command calling fct with {a2}")
            r=fct(a2)
            if (r>0):
                trace(3,f"{fct.__name__} command successful for user {ue}") 
            else:
                trace(1,f"{fct.__name__} command failed for user {ue}")
            time.sleep(0.01)



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

    trace (3, f"In uid_to_grp {cmd}, {uid} , {gid} ")
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
        trace(1,f"user_to_grp: Failed to find user email {ue}") 
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
    m = re.search(".*\.csv$", a[0])
    if (m):
        user_csv_command(add_user_to_grp, a)
    else:
        add_user_to_grp(a)

def uf_del_user_to_grp(a):
    m = re.search(".*\.csv$", a[0])
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
    
    trace(3,f"in get_user_vm {a}")

    uid=get_user_id(ue)

    trace(3,f"get_user_vm: got id {uid}")

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
            trace(3, f"success for get_user_vm {ue} : got {j}")  
            return(j)
        else:
            trace(1, f"got error {s}: {r.reason}")  


# Enables VM for given user email with given json body
# returns 1 on success, negative value on failure 
#
def set_user_vm(a):
    (ue)=(a[0])
    (body)=(a[1])

    trace(3,f"in set_user_vm {a}")

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
        trace(1,f"get_user_id {ue} error ") 
        return(-2)

# Enables VM for given user email based on another user email 'template'
# returns set_user_vm status or -1 if base user not found
#
def set_user_vm_based_on_other_user(a):
    (ue, be)=(a[0], a[1])

    trace(3,f"in set_user_vm_based_on_other_user {a}")

    tmpl=get_user_vm([be])
    if ( tmpl ):
        # replace other email with target email
        bdy=tmpl.replace(be, ue)
        a=[ue,bdy]
        return (set_user_vm(a))
    else:
        trace(1,"get_user_vm error")
        return(-1)

def add_vm(a): 
    set_user_vm_based_on_other_user(a)

def uf_add_vm_csv(a): 
    m = re.search(".*\.csv$", a[0])
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
    trace(3,f"in delete_user {a}")

    uid=get_user_id(ue)
    if (uid): 
        url=f"https://webexapis.com/v1/people/{uid}"
        r = requests.request("DELETE", url, headers=setHeaders())
        s = r.status_code
        if s == 204 :
            trace (2, f"User {ue} deleted ")
            return(1)
        else:
            trace(1,f"del_user : Error {s}")  
            trace(1,r.text.encode('utf8'))
            return(-1)
    else:
        trace (1, f"del_user: {ue} not found")  
        return(-1)
    
def uf_del_user(a):
    m = re.search(".*\.csv$", a[0])
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
    trace(3,f"in deactivate_user {a}")
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
    m = re.search(".*\.csv$", a[1])
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
        trace (2, f" Auth {aid} deleted")
        return(1)
    else :
        trace(1,f" del_user_auth : Error {s}")  
        trace(1,r.text.encode('utf8'))
        return(-1)

# cmd "list" : prints auths for user email
# cmd "get" : returns items obj as per wbx API 
# retuuns 1 if happy 
#
def user_auths(cmd, a): 
    ue=a[0]
    trace(3,f"in reset_user {ue}")
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
            trace(1,f" reset_user : Error {s}")  
            trace(1,r.text.encode('utf8'))
            return(-1)
    else:
        trace (1, f"reset_user: {ue} not found")  
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
    m = re.search(".*\.csv$", a[0])
    if (m):
        user_csv_command(uf_list_user_auths, a, 0)
    else:
        return(user_auths("list", a))
    

# reset all access for user email passed as array 
# ( user facing )
def uf_del_user_auths(a):
    m = re.search(".*\.csv$", a[0])
    if (m):
        user_csv_command(del_all_user_auths, a)
    else:
        user_auths("del", a) 


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
    }
}


def main():

    # print(args)

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
    if (len(args.parameters) == len(par_arr)):
        # call function associated with command 
        fct=syntax[cmd1][cmd2]['fct']
        trace(3,f"in main: calling {fct.__name__} with {args.parameters}")
        fct(args.parameters)
    else:
        print("Incorrect parameters. Check syntax ")
        print_syntax()
    #
   
main()
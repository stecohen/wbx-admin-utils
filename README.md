# wbx-admin-utils

## Usage:
python3 -m wbx_admin_utils [options] command subcommand [parameters]

## Commands list and syntax:
```
python3 -m wbx_admin_utils help commands 
```

## Commands:
```
help
   commands : display list of available commands
group
   list : list all groups in admin org
   list-users <group_id> : list user ids (max 500) in given group id
   add-user <email|csvFile> <group_id> : add user in given group id
   remove-user <email|csvFile> <group_id> : remove user from given group id
user
   details <email|user_id> : print user details in json
   tokens <email|csvFile> : list user(s) access token
   reset <email|csvFile> : reset user(s) access token
   activate <Yes|No> <email|csvFile> : activate (Yes) or deactivate (No) user(s)
   delete <email|csvFile> : delete user(s)
   get-vm <email> : dump user voicemail settings in json format
   add-vm <email|csvFile> <base user email> : set user(s) voicemail options based on another user's voicemail settings
```

## Options:
* -t \<token\> Adds access token as a parameter. Will be read from AUTH_BEARER Env Variable by defaut. Yyou can get your personal access token from [webex developper](https://developer.webex.com/docs/getting-your-personal-access-token)
* -d \<debugLevel> from 0 to 3 (most verbose). Default is 2 (info level)    

## Examples:
* Python3 -m wbx_admin_utils group list            
* Python3 -m wbx_admin_utils group list-users ``<groupid>``
* Python3 -m wbx_admin_utils group add-user user1@customer.com ``<groupid\>``
* Python3 -m wbx_admin_utils group remove-user /tmp/users.csv ``<groupid>``
* Python3 -m wbx_admin_utils user reset-access /tmp/users.csv
* Python3 -m wbx_admin_utils user deactivate /tmp/users.csv

## CSV input file format:
```
email, comments 
user1@customer.com, some optinal info about user1 
user2@customer.com, some optinal info about user1 
```
The first column is currenlty processed and must be titled 'email' other columns are optional and ignored.



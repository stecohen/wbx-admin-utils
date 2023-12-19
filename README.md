## Usage:
( You might need to replace "python3" for "python3" )
```
python3 -m wbx_admin_utils [options] command subcommand [parameters]
python3 -m wbx_admin_utils help commands # shows the full list of available commmands

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
co
   list-messages <email, 'options'> : list messages sent by a user
   list-space-members <id> : list menbers in space
```

## Options:
* -t \<token\> Adds access token as a parameter. Will be read from AUTH_BEARER Env Variable by defaut. Yyou can get your personal access token from [webex developper](https://developer.webex.com/docs/getting-your-personal-access-token)
* -d \<debugLevel> from 0 to 3 (most verbose). Default is 2 (info level)

## co (compliance officer) commands 
* list-messages option format is in json format as per the 'event' API command 
* all results are displayed in .CSV format 

## Examples:
```
# List user groups in CH Org
python3 -m wbx_admin_utils group list

# List users in group id
python3 -m wbx_admin_utils group list-users ``<groupid>``

# Add or remove users in specified group id
python3 -m wbx_admin_utils group add-user user1@customer.com ``<groupid>``
python3 -m wbx_admin_utils group remove-user /tmp/users.csv ``<groupid>``

# Reset (force log-out) user access tokens
python3 -m wbx_admin_utils user reset /tmp/users.csv

# Activate or deactivate users
python3 -m wbx_admin_utils user activate Yes user1@customer.com
python3 -m wbx_admin_utils user activate No /tmp/users.csv

# list messages sent by user (default from = 30 days ago, default to = today)
python3 -m wbx_admin_utils co list-messages user1@customer.com > report.csv 
python3 -m wbx_admin_utils co list-messages user1@customer.com '{"from":"2022-10-20T00:00:00.000Z", "to":"2023-10-20T00:00:00.000Z" }'

# list members of a space  
python3 -m wbx_admin_utils co list-space-members <spaceid>

```


## CSV input file format:
```
email, comments
user1@customer.com, some optinal info about user1
user2@customer.com, some optinal info about user1
```
The first column is currenlty processed and must be titled 'email' other columns are optional and ignored.
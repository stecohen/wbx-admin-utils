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
   commands : display the list of commands
group
   list : list all groups in admin org
   list-users <group_id> : list user ids in given group id
   add-user <email> <group_id> : add user email in given group id
   add-users-in-csv <file> <group_id> : add user listed in CSV file in given group id
   remove-user <email> <group_id> : remove user email from given group id
   remove-users-in-csv <file> <group_id> : remove users listed in CSV file in given group id
user
   list-user-tokens <email> : list user access token
   list-user-tokens-csv <file> : list access tokens for users in csv file
   reset-access <email> : reset user access token
   reset-access-csv <file> : reset user access token from CSV
   delete-user <email> : delete user
   delete-users-csv <file> : delete users listed via email address in given CSV file
   get-voicemail <email> : dump user voicemail settings in json format
   add-voicemail <email> <base user email> : set user voicemail options based on another user's voicemail settings
   add-voicemail-csv <file> <base user email> : set voicemail options based on another user's voicemail settings for all users listed in CSV file
```

## Options:
* -t \<token\> Adds access token as a parameter. Will be read from AUTH_BEARER Env Variable by default
* -d \<debugLevel> from "0" to "3" (most verbose). Default is "1" to print errors only    

## Examples:
* Python3 -m wbx_admin_utils group list            
* Python3 -m wbx_admin_utils group list-users \<groupid\>
* Python3 -m wbx_admin_utils user list-users reset-access-csv /tmp/user.csv

## CSV input file format:
```
email, comments 
user1@customer.com, some optinal info about user1 
user2@customer.com, some optinal info about user1 
```
The first column is currenlty processed other columns are optional and ignored.



Get Group Info
API Description
Use this API to retrieve the group info of a group chat which the bot has been added to.

Note:

To call this API, your app must enable the bot capability and have an Online status. See more at Quickly build a Bot.
This API requires Get Group Info permission and the relevant Availability scope.
This API is limited to 100 requests per minute under one app ID.
Request Method: GET

End Point: https://openapi.seatalk.io/messaging/v2/group_chat/info

Request Parameter
Header

Parameter

Type

Mandatory

Description

Default

Sample

Authorization

string

Yes

Obtained through the Get App Access Token API

N/A

Bearer c8bda0f77ef940c5bea9f23b2d7fc0d8

Parameter

Parameter

Type

Mandatory

Description

Default

Sample

group_id

string

Yes

The group chat ID

N/A

"abcdef"

page_size

int

No

- Pagination Feature will be applied to "group_user_list", "group_bot_list" and "group_system_account_list" lists.

- page_size defines the number of items included in one response for each list. It must be an integer between 1-100 (inclusive).

50

50

cursor

string

No

Cursor info from previous request. It is not filled in the first request. Use this info to indicate where to start traversal; The next "cursor" will be returned in the response of current request

N/A

gmrdPA7cyZP2qGJkM-hatoA7SySeNmOlDyv8x1p9K0pxvJPxs_qL5Y2OL2-Dkoq1VH_FtDccHq5GrpzuMK4pyw==

Request Sample

https://openapi.seatalk.io/messaging/v2/group_chat/info?group_id=abcdef

Copy
Response Parameter
Result Fields

Parameter

Type

Description 

code

int

Refer to Error Code for explanation

next_cursor    

string

Cursor info for the next request. Put it in the "cursor" field in the next request. If the cursor is empty, it means there is no next request to be called.

group

object

 

∟group_name

string

Current group chat name

∟group_settings

object

 

  ∟chat_history_for_new_members

string

The extent to which the new group member can access the chat histories sent prior to joining. Possible values are "disabled", "1 day" and "7 days".

  ∟can_notify_with_at_all

boolean

Whether group members are allowed to notify all group members with “@All”

  ∟can_view_member_list

boolean

Whether group members are allowed to view the group member list

∟group_user_total

int

- Number of normal users in the group

- Return empty if the member list has been hidden for this group.

∟group_bot_total

int

- Number of bots in the group

- Return empty if the member list has been hidden for this group.

∟group_system_account_total

int

- Number of system accounts in the group

- Return empty if the member list has been hidden for this group.

∟group_user_list

[]object

- List of normal users in the group

- Return empty if the member list has been hidden for this group.

  ∟seatalk_id

string

The SeaTalk ID of the normal user.

  ∟employee_code  

string

- The employee code of the normal user.

- Return empty when the user and the bot do not belong to the same organisation.

  ∟email

string

- The email of the normal user.

- Return empty when the user and the bot do not belong to the same organisation.

∟group_bot_list

[]string

- List of bots in the group: The SeaTalk ID of the bot.

- Return empty if the member list has been hidden for this group.

∟group_system_account_list

[]string

- List of system accounts in the group: The SeaTalk ID of the system account.

- Return empty if the member list has been hidden for this group.

Response Sample

{
  "code": 0,
  "next_cursor": "",
  "group": {
    "group_name": "Test Group",
    "group_settings": {
      "chat_history_for_new_members": "7 days",
      "can_notify_with_at_all": true,
      "can_view_member_list": true
    },
    "group_user_total": 1,
    "group_bot_total": 2,
    "group_system_account_total": 0,
    "group_user_list": [
      {
        "seatalk_id": "12345678",
        "employee_code": "e_293847124"
        "email": "sample@seatalk.biz"
      }
    ],
    "group_bot_list": [
      "23456789",
      "34567890"
    ],
    "group_system_account_list": []
  }
}

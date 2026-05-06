Send Message to Group Chat
API Description
Send a message to a group chat that the bot is a member of. Currently, you can leverage this API to send text messages with/without formatting, images, files, and interactive messages.

Starting from 11 June 2024, the API can be used to send a reply to a thread by providing a thread_id in the request. (Learn more about threading messages in group chats)

The end user has to be on app version 3.44.5 or above, releasing on 14 June 2024, to interact with bots in threads with full functionalities.
Note:

To call this API, your app must enable the bot capability and have an Online status. See more at Quickly build a Bot.
This API requires Send Message to Group Chat permission and the relevant Availability scope.
This API is limited to 100 requests per minute and  20 requests per second under one app ID.
This API is subject to a daily per-chat message limit shared by all bots and system accounts in the same chat. After the limit is reached, bots and system accounts will be unable to send messages in this chat until the next day.

Request Method: POST

End Point: https://openapi.seatalk.io/messaging/v2/group_chat

Send a Text Message with/without Formatting
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

Content-Type

string

Yes

Request header format

N/A

application/json

Body

Parameter

Type

Mandatory

Description

Default Value

Length Limit

Sample

group_id

string

Yes

The group chat ID

N/A

N/A

“abcdef”

message

object

Yes

The message to be sent

N/A

N/A

 

∟tag

string

Yes

The type of the message - be it "text" in this case

N/A

N/A

“text”

∟text

object

Yes

The text message object

N/A

N/A

 

  ∟format

int

No

The formatting to use in the content of the text message. Can be:

1: Formatted text message (Markdown)

2: Plain text message

1

N/A

1

  ∟content

string

Yes

- The content of the message with markdown syntax supported

- Refer to this document for supported markdown elements

N/A

Min: 1 character

Max: 4096 characters

 

∟quoted_message_id

string

No

The message id if you would like the bot to quote a message to reply

Notes:

- Only quoting messages sent within the last 7 days is supported.

- For security reasons, a single message will have different message_ids when accessed by different apps.

N/A

N/A

 

∟thread_id

string

No

 

Effective from 11 June 2024.

The thread ID. Provide thread_id to send message as a thread reply.

 

To start a thread in an unthreaded root message, define thread_id as the message_id of the root message.
The root message has to be sent within the past 7 days.
 

N/A

N/A

 

Request Sample

{
    "group_id":"abcdefgh",
    "message":{
        "tag":"text",
        "text":{
            "format":1,
            "content":"Kindly note there's **no meeting** today <mention-tag target=\"seatalk://user?id=0\"/>."
        },
        "quoted_message_id":"bcdef",
        "thread_id":"hjsatc"
    }
}

Copy
Response Parameter
Result Field

Parameter

Type

Description 

code

int

Refer to Error Code for explanation.

message_id

string

The ID of the message if it has been successfully sent out.

Note: For security reasons, a single message will have different message_ids when accessed by different apps.

Send an Image Message 
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

Content-Type

string

Yes

Request header format

N/A

application/json

Body

Parameter

Type

Mandatory

Length Limit

Description

Default

Sample

group_id

string

Yes

N/A

The group chat ID

N/A

“abcdef”

message

object

Yes

N/A

The message to be sent

N/A

 

∟tag

string

Yes

N/A

The type of the message, in this case, is 'image'.

N/A

“image”

∟image

object

Yes

N/A

The image message object

N/A

 

  ∟content

string

Yes

Maximum 5MB after encoding

- The Base64-encoded image file

- Only PNG, JPG and GIF images are supported

N/A

 

∟quoted_message_id

string

No

N/A

The message id if you would like the bot to quote a message to reply

Note:

- Only quoting messages sent within the last 7 days is supported.

- For security reasons, a single message will have different message_ids when accessed by different apps.

N/A

∟thread_id

string

No

N/A

 

Effective from 11 June 2024.

The thread ID. Provide thread_id to send message as a thread reply.

 

To start a thread in an unthreaded root message, define thread_id as the message_id of the root message.
The root message has to be sent within the past 7 days.
 

 

 

Request Sample

{
    "group_id":"abcdefgh",
    "message":{
        "tag":"image",
        "image":{
            "content":"iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVQYV2P8/uPnfwYGBgZGGAMAVe4H0WDm+2kAAAAASUVORK5CYII="
        }
    }
}

Copy
Response Parameter
Result Field

Parameter

Type

Description 

code

int

Refer to Error Code for explanation.

message_id

string

- The ID of the message if it has been successfully sent out.

- For security reasons, a single message will have different message_ids when accessed by different apps.

Send an Interactive Message
Requires SeaTalk App version 3.38.1 or later
Request parameter
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

Content-Type

string

Yes

Request header format

N/A

application/json

Body

Parameter

Type

Mandatory

Length Limit

Description

group_id

string

Yes

N/A

The group chat ID

message

object

Yes

N/A

The message to be sent

∟tag

string

Yes

N/A

The type of the message, in this case, is 'interactive_message'.

∟interactive_message

object

Yes

N/A

The interactive message object

∟elements

object

Yes

N/A

- The message object whose structure depends on the specified "tag" field

- For a comprehensive introduction to building an interactive message card, see Build a Card

∟thread_id

string

No

N/A

 

Effective from 11 June 2024.

The thread ID. Provide thread_id to send message as a thread reply.

 

To start a thread in an unthreaded root message, define thread_id as the message_id of the root message.
The root message has to be sent within the past 7 days.
 

Request Sample
{
    "group_id":"ODE1ODE2NTI5MjIx",
    "message":{
        "tag":"interactive_message",
        "interactive_message":{
            "elements":[
                {
                    "element_type":"title",
                    "title":{
                        "text":"Interactive Message Title"
                    }
                },
                {
                    "element_type":"description",
                    "description":{
                        "format": 1,
                        "text":"Interactive Message Description"
                    }
                },
                {
                    "element_type":"button",
                    "button":{
                        "button_type":"callback",
                        "text":"Callback Button",
                        "value":"test"
                    }
                },
                {
                    "element_type":"button",
                    "button":{
                        "button_type":"redirect",
                        "text":"rn link",
                        "mobile_link":{
                            "type":"rn",
                            "path":"/webview",
                            "params":{
                                
                            }
                        }
                    }
                }
            ]
        }
    }
}

Copy
Response Parameter
Result Fields
Parameters

Type

Description

code

int

Refer to Error Code for explanations

message_id

string

The id of the sent out message

Note: For security reasons, a single message will have different message_ids when accessed by different apps.

Response Sample
{
    "code":0,
    "message_id":"uFrIUn3uDAIRQpReXQ0G6T8fxG0duqp67smFLmG5cwU"
}

Copy
Send a File Message
Requires SeaTalk App version 3.41.0 or later
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

Content-Type

string

Yes

Request header format

N/A

application/json

Body
Parameter

Type

Mandatory

Length Limit

Description

Default

Sample

group_id

string

Yes

N/A

The group chat ID

N/A

“abcdef”

message

object

Yes

N/A

The message to be sent

N/A

 

∟tag

string

Yes

N/A

The type of the message, in this case, is 'file'.

N/A

“file”

∟file

object

Yes

N/A

The file message object

N/A

 

  ∟content

string

Yes

Maximum 5MB and Minimum 10B after encoding

- The Base64-encoded file

- All file types are supported including Images (only PNG, JPG, and GIF have preview in client)

N/A

"VGhpcyBpcyBhIGRlbW8gdGV4dCBmaWxlLgo="

  ∟filename

string

Yes

100 characters

The file name with extension; files with no extension specified will be sent as unidentified files

N/A

"demo.txt"

∟quoted_message_id

string

No

N/A

The message id if you would like the bot to quote a message to reply

Note:

- Only quoting messages sent within the last 7 days is supported.

- For security reasons, a single message will have different message_ids when accessed by different apps.

N/A

“bcdefg”

∟thread_id

string

No

N/A

 

Effective from 11 June 2024.

The thread ID. Provide thread_id to send message as a thread reply.

 

To start a thread in an unthreaded root message, define thread_id as the message_id of the root message.
The root message has to be sent within the past 7 days.
 

N/A

 

Request Sample
{
    "group_id":"abcdefgh",
    "message":{
        "tag":"file",
        "file":{
            "filename":"demo.txt",
            "content":"VGhpcyBpcyBhIGRlbW8gdGV4dCBmaWxlLgo="
        }
    }
}

Copy
Response Parameter
Result Field
Parameter

Type

Description 

code

int

Refer to Error Code for explanation.

message_id

string

- The ID of the message if it has been successfully sent out.

- For security reasons, a single message will have different message_ids when accessed by different apps.

Response Sample
{
    "code":0,
    "message_id":"uFrIUn3uDAIRQpReXQ0G6T8fxG0duqp67smFLmG5cwU"
}

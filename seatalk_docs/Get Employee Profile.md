Get Employee Profile
API Description
Use this API to obtain an employee's basic profile information.

Note:

This API requires Get Contact Profile permission and the relevant Data Scope. 
Request Method: GET

End Point: https://openapi.seatalk.io/contacts/v2/profile

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

Size Limit

Sample

employee_code

string

Yes

One or more employee_code(s)

N/A

Maximum: 500

"123"

Request Sample

https://openapi.seatalk.io/contacts/v2/profile?employee_code=123&employee_code=456

Copy
Response Parameter
Result Fields

Parameters

Type

Description

code

int

Refer to Error Code for explanations

employees

[]object

The info of the employee

∟employee_code

string

The employee_code of the employee

∟seatalk_id

string

The SeaTalk ID of the employee

∟seatalk_nickname

string

The SeaTalk nickname of the employee

∟avatar

string

The SeaTalk avatar of the employee

∟name

string

The name of the employee in the organization

∟email

string

The email of the employee

∟departments

[]string

The code of the departments the employee are under

∟gender

int

The gender of the employee

0: Blank

1: Male

2: Female

3. Unknown

∟mobile

string

The mobile phone number of the employee

∟reporting_manager_employee_code

string

The employee_code of the employee's reporting manager

0 if not applicable

∟offboarding_time

int

The time when termination is triggered, the employee status changes from "In Position" to "Terminated".

Response Sample

{
  "code": 0,
  "employees": [
    {
      "employee_code": "e_t9e4bbys",
      "name": "Zhan Peng (詹鹏)",
      "email": "peng.zhan@shopee.com",
      "mobile": "",
      "seatalk_id": "9339874886",
      "seatalk_nickname": "Zhan Peng (詹鹏)",
      "avatar": "https://openapi.seatalk.io/file/employee/icon/5104fb0142a8c50816956645450f19a50b03010000022b3a00000000020200ef",
      "departments": [
        "12345"
      ],
      "gender": 1,
      "reporting_manager_employee_code": "",
      "offboarding_time": "1718074364", 
      "custom_fields": [
        {
          "name": "座位号",
          "type": 0,
          "value": "",
          "link_entry_icons": [],
          "link_entry_text": ""
        },
        {
          "name": "github",
          "type": 1,
          "value": "",
          "link_entry_icons": [],
          "link_entry_text": ""
        },
        {
          "name": "测试测试",
          "type": 2,
          "value": "",
          "link_entry_icons": [],
          "link_entry_text": ""
        }
      ]
    }
  ]
}

# SeaTalk Overbreak Alert Bot

A Python server that monitors Google Sheets for overbreak data and sends formatted alerts to SeaTalk group chats.

## Features

- **Automated Monitoring**: Checks `workstation_dump!A3:G3` for new data every 30 seconds
- **Timestamp Automation**: Automatically records timestamp in `attendance_timein_data!N2` when data is detected
- **SeaTalk Integration**: Sends formatted messages with bold headers and user mentions
- **Configurable**: Environment-based configuration for easy deployment

## Message Format

When data is detected, the bot sends:

```
**Inbound Overbreak Monitoring**
as of [timestamp]

>1 HR = [value from N4]
**Ops _id list of Overbreak**
[value from M6] - [value from O6]

cc: @mention(user1) @mention(user2) @mention(user3)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|----------|-------------|
| `SEATALK_ACCESS_TOKEN` | Your SeaTalk bot access token |
| `SEATALK_GROUP_ID` | Target group chat ID |
| `GOOGLE_SHEET_ID` | Google Sheet ID (default provided) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to service account JSON |

### 3. Configure SeaTalk Bot

1. Create a bot in SeaTalk Open Platform
2. Enable permissions:
   - "Send Message to Group Chat"
   - "Get Group Info"
   - "Event Callback" (for webhooks)
3. Configure webhook URL in SeaTalk Open Platform:
   - URL: `https://your-server.com/webhook`
   - Copy the **Signing Secret** to your `.env` file
4. Add the bot to your target group chat
5. The bot will automatically store the group ID in the **"groupid" sheet tab**

**Note**: The bot will automatically detect when it's added to a group and store the `group_id` in the Google Sheet. You can omit `SEATALK_GROUP_ID` from `.env` if the bot auto-joins the group.

### 4. Configure Google Sheets

Ensure your service account has access to the spreadsheet:
1. Share the Google Sheet with the service account email (found in `google-service-account.json`)
2. Grant Editor permissions

### 5. Run the Server

```bash
python seatalk_bot.py
```

The server will start on port 5000 by default.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | Receive SeaTalk webhooks |
| `/health` | GET | Health check |
| `/trigger-check` | POST | Manually trigger a sheet check |
| `/send-test-message` | POST | Send a test message to the group |
| `/groups` | GET | List all stored groups |

### Group Storage

When the bot is added to a group chat, the `bot_added_to_group_chat` webhook triggers and the bot:
1. Calls the **Get Group Info API** to fetch full group details
2. Stores the group info in the **"groupid" sheet tab** (columns: A=group_id, B=group_name, C=added_at)
3. Auto-configures `group_id` if not already set

**Stored Group Info:**
```json
{
  "group_id": "ODE1ODE2NTI5MjIx",
  "group_name": "Ops Overbreak Alerts",
  "group_settings": {...},
  "group_user_total": 15,
  "group_bot_total": 1,
  "added_at": "2026-05-06T16:00:00",
  "inviter": {
    "seatalk_id": "1234567890",
    "employee_code": "e_12345678",
    "email": "user@example.com"
  }
}
```

### List Stored Groups

```bash
curl http://localhost:5000/groups
```

### Manual Trigger Example

```bash
curl -X POST http://localhost:5000/trigger-check
```

### Send Test Message Example

```bash
curl -X POST http://localhost:5000/send-test-message \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

## Sheet Structure

The bot expects these named ranges/sheets:

- `workstation_dump!A3:G3` - Monitored range for new data
- `[do_not_edit] attendance_timein_data!N2` - Timestamp cell
- `[do_not_edit] attendance_timein_data!N4` - Overbreak count cell
- `Ops _id list of Overbreak!M6` - First ops ID
- `Ops _id list of Overbreak!O6` - Second ops ID

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Google Sheets  │◄────│  Overbreak Bot  │────►│   SeaTalk API   │
│                 │     │                 │     │                 │
│ workstation_dump│     │  • Scheduler    │     │  Group Chat     │
│ attendance_data │     │  • Monitor      │     │                 │
│ Ops _id list    │     │  • SeaTalk      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Troubleshooting

### Bot can't access sheet
- Verify service account email has been added as an editor to the Google Sheet
- Check `google-service-account.json` is in the correct location

### Messages not sending
- Verify `SEATALK_ACCESS_TOKEN` is valid and not expired
- Confirm bot is a member of the target group chat
- Check bot has "Send Message to Group Chat" permission

### Webhook not receiving events
- Ensure your server is publicly accessible (use ngrok for local testing)
- Register webhook URL in SeaTalk Open Platform

## License

Internal use only.

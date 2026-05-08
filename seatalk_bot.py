"""
SeaTalk Bot Server for Overbreak Alerts
Monitors Google Sheets and sends alerts to SeaTalk group chat.
"""

import os
import time
import json
import base64
import hashlib
import logging
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
import schedule
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Event Types (from SeaTalk Event Callback docs)
EVENT_VERIFICATION = "event_verification"
NEW_BOT_SUBSCRIBER = "new_bot_subscriber"
MESSAGE_FROM_BOT_SUBSCRIBER = "message_from_bot_subscriber"
INTERACTIVE_MESSAGE_CLICK = "interactive_message_click"
BOT_ADDED_TO_GROUP_CHAT = "bot_added_to_group_chat"
BOT_REMOVED_FROM_GROUP_CHAT = "bot_removed_from_group_chat"
NEW_MENTIONED_MESSAGE_RECEIVED_FROM_GROUP_CHAT = "new_mentioned_message_received_from_group_chat"


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)


class GoogleSheetsClient:
    """Client for interacting with Google Sheets API."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, service_account_file: str, sheet_id: str):
        self.sheet_id = sheet_id
        
        # Support loading from file or environment variable
        env_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
        
        if env_json:
            # Load from environment variable (for Render deployment)
            try:
                service_account_info = json.loads(env_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=self.SCOPES
                )
                logger.info("Loaded Google credentials from environment variable")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                raise
        elif os.path.exists(service_account_file):
            # Load from file (for local development)
            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.SCOPES
            )
            logger.info(f"Loaded Google credentials from file: {service_account_file}")
        else:
            raise FileNotFoundError(
                f"Google service account file not found: {service_account_file}. "
                "Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable or ensure file exists."
            )
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheets = self.service.spreadsheets()
        
    def get_values(self, range_name: str) -> Optional[List[List[str]]]:
        """Get values from a specific range."""
        try:
            result = self.sheets.values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except Exception as e:
            logger.error(f"Error getting values from {range_name}: {e}")
            return None
    
    def update_value(self, range_name: str, value: str) -> bool:
        """Update a single cell value."""
        try:
            body = {
                'values': [[value]]
            }
            self.sheets.values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            logger.info(f"Updated {range_name} with value: {value}")
            return True
        except Exception as e:
            logger.error(f"Error updating {range_name}: {e}")
            return False

    def update_values(self, range_name: str, values: List[List[str]]) -> bool:
        """Update a range with multiple rows."""
        try:
            body = {
                'values': values
            }
            self.sheets.values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            logger.info(f"Updated {range_name} with {len(values)} rows")
            return True
        except Exception as e:
            logger.error(f"Error updating {range_name}: {e}")
            return False
    
    def is_range_not_empty(self, range_name: str) -> bool:
        """Check if a range has any non-empty values."""
        values = self.get_values(range_name)
        if not values:
            return False
        for row in values:
            for cell in row:
                if cell and cell.strip():
                    return True
        return False


class SeaTalkClient:
    """Client for interacting with SeaTalk API."""
    
    BASE_URL = "https://openapi.seatalk.io"
    TOKEN_REFRESH_BUFFER = 300  # Refresh 5 minutes before expiry
    
    def __init__(self, app_id: str, app_secret: str, access_token: Optional[str] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.token_expiry = 0
        
        if not self.access_token:
            self._fetch_access_token()
        
    def _get_headers(self) -> Dict[str, str]:
        self._ensure_valid_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _fetch_access_token(self) -> bool:
        """Fetch a new access token using app_id and app_secret."""
        url = f"{self.BASE_URL}/auth/app_access_token"
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result.get('app_access_token')
                self.token_expiry = result.get('expire', 0)
                logger.info("Successfully fetched new access token")
                return True
            else:
                logger.error(f"Failed to fetch token: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return False
    
    def _ensure_valid_token(self):
        """Ensure the access token is still valid, refresh if needed."""
        current_time = int(time.time())
        
        if not self.access_token or current_time >= (self.token_expiry - self.TOKEN_REFRESH_BUFFER):
            logger.info("Access token expired or expiring soon, refreshing...")
            self._fetch_access_token()
    
    def send_text_message(self, group_id: str, content: str, 
                         format_type: int = 1) -> Optional[Dict[str, Any]]:
        """
        Send a text message to a group chat.
        format_type: 1 = Markdown formatted, 2 = Plain text
        """
        url = f"{self.BASE_URL}/messaging/v2/group_chat"
        
        payload = {
            "group_id": group_id,
            "message": {
                "tag": "text",
                "text": {
                    "format": format_type,
                    "content": content
                }
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Message sent successfully. Message ID: {result.get('message_id')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def get_group_info(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a group chat."""
        url = f"{self.BASE_URL}/messaging/v2/group_chat/info"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params={"group_id": group_id},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting group info: {e}")
            return None


class GroupStorage:
    """Manages storage of group information in Google Sheets tab 'group_id'."""
    
    SHEET_NAME = "group_id"
    SHEET_RANGE = "group_id!A2:C"  # A: group_id, B: group_name, C: added_at
    
    def __init__(self, sheets_client: GoogleSheetsClient, sheet_id: str):
        self.sheets = sheets_client
        self.sheet_id = sheet_id
        self.groups = self._load_groups()
    
    def _load_groups(self) -> Dict[str, Any]:
        """Load groups from Google Sheets 'group_id' tab."""
        try:
            values = self.sheets.get_values(self.SHEET_RANGE)
            groups = []
            if values:
                for row in values:
                    if len(row) >= 1 and row[0]:
                        group = {
                            "group_id": row[0].strip(),
                            "group_name": row[1] if len(row) > 1 else "",
                            "added_at": row[2] if len(row) > 2 else ""
                        }
                        groups.append(group)
            logger.info(f"Loaded {len(groups)} groups from sheet tab '{self.SHEET_NAME}'")
            return {"groups": groups}
        except Exception as e:
            logger.error(f"Error loading groups from sheet: {e}")
            return {"groups": []}
    
    def _save_groups(self):
        """Save groups to Google Sheets 'group_id' tab."""
        try:
            # Prepare data with header
            values = [["group_id", "group_name", "added_at"]]
            for group in self.groups.get("groups", []):
                values.append([
                    group.get("group_id", ""),
                    group.get("group_name", ""),
                    group.get("added_at", "")
                ])
            
            # Clear and update range
            self.sheets.update_values(f"{self.SHEET_NAME}!A1", values)
            logger.info(f"Groups saved to sheet tab '{self.SHEET_NAME}'")
        except Exception as e:
            logger.error(f"Error saving groups to sheet: {e}")
    
    def add_group(self, group_info: Dict[str, Any]):
        """Add or update a group in storage."""
        group_id = group_info.get('group_id')
        
        # Check if group already exists
        existing = False
        for i, group in enumerate(self.groups["groups"]):
            if group.get('group_id') == group_id:
                self.groups["groups"][i] = group_info
                existing = True
                logger.info(f"Updated existing group: {group_id}")
                break
        
        if not existing:
            self.groups["groups"].append(group_info)
            logger.info(f"Added new group: {group_id}")
        
        self._save_groups()
    
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific group by ID."""
        for group in self.groups["groups"]:
            if group.get('group_id') == group_id:
                return group
        return None
    
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get all stored groups."""
        return self.groups.get("groups", [])

    def refresh(self):
        """Reload groups from the sheet."""
        self.groups = self._load_groups()

    def get_group_ids(self) -> List[str]:
        """Get all non-empty group IDs from storage."""
        group_ids = []
        seen = set()
        for group in self.get_all_groups():
            group_id = group.get('group_id', '').strip()
            if group_id and group_id not in seen:
                group_ids.append(group_id)
                seen.add(group_id)
        return group_ids
    
    def get_primary_group_id(self) -> Optional[str]:
        """Get the first/primary group ID from storage."""
        groups = self.get_all_groups()
        if groups:
            return groups[0].get('group_id')
        return None
    
    def remove_group(self, group_id: str) -> bool:
        """Remove a group from storage."""
        for i, group in enumerate(self.groups["groups"]):
            if group.get('group_id') == group_id:
                removed = self.groups["groups"].pop(i)
                self._save_groups()
                logger.info(f"Removed group: {group_id}")
                return True
        return False


monitor = None
group_storage = None
scheduler_running = False


def init_monitor():
    """Initialize the monitor and group storage."""
    global monitor, group_storage
    
    # Create sheets client first (needed for GroupStorage)
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'google-service-account.json')
    sheets_client = GoogleSheetsClient(service_account_file, sheet_id)
    
    # Initialize GroupStorage with sheets client
    group_storage = GroupStorage(sheets_client, sheet_id)
    
    # Initialize OverbreakMonitor (reuses sheets_client)
    monitor = OverbreakMonitor(sheets_client)
    logger.info("OverbreakMonitor and GroupStorage initialized.")


class OverbreakMonitor:
    """Monitors Google Sheets for overbreak data and sends SeaTalk alerts."""
    
    # Sheet ranges
    WORKSTATION_DUMP_RANGE = "workstation_dump!A3:I3"
    TIMESTAMP_CELL = "[do_not_edit] attendance_timein_data!N2"
    OVERBREAK_COUNT_CELL = "[do_not_edit] attendance_timein_data!N4"
    OPS_ID_CELL_1 = "Ops _id list of Overbreak!M6"
    OPS_ID_CELL_2 = "Ops _id list of Overbreak!O6"
    NO_BREAKTIME_SCAN_RANGE = "Ops _id list of Overbreak!P2:P50"
    ONGOING_BREAKTIME_RANGE = "Ops _id list of Overbreak!R2:R50"
    
    def __init__(self, sheets_client: GoogleSheetsClient = None):
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.seatalk_app_id = os.getenv('SEATALK_APP_ID')
        self.seatalk_app_secret = os.getenv('SEATALK_APP_SECRET')
        self.seatalk_token = os.getenv('SEATALK_ACCESS_TOKEN')
        self.group_id = None
        
        # Use env group_id or fall back to stored primary group
        env_group_id = os.getenv('SEATALK_GROUP_ID')
        if env_group_id:
            self.group_id = env_group_id
            logger.info(f"Using SEATALK_GROUP_ID from environment: {self.group_id}")
        elif group_storage:
            self.group_id = group_storage.get_primary_group_id()
            if self.group_id:
                logger.info(f"Using group_id from storage: {self.group_id}")
        
        if not self.group_id:
            logger.warning("No group_id configured! Bot will not be able to send messages.")
            self.group_id = None
            
        self.cc_user_ids = os.getenv('CC_USER_IDS', '').split(',')
        
        self.delay_seconds = int(os.getenv('DELAY_BEFORE_SEND_SECONDS', '5'))
        
        # Use provided sheets_client or create new one
        if sheets_client:
            self.sheets_client = sheets_client
        else:
            service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'google-service-account.json')
            self.sheets_client = GoogleSheetsClient(service_account_file, self.sheet_id)
            
        self.seatalk_client = SeaTalkClient(
            self.seatalk_app_id,
            self.seatalk_app_secret,
            self.seatalk_token
        )
        
        self.last_check_had_data = False
        
    def _format_mentions(self, user_ids: List[str]) -> str:
        """Format user mentions for SeaTalk markdown."""
        mentions = []
        for user_id in user_ids:
            user_id = user_id.strip()
            if user_id:
                mentions.append(f'<mention-tag target="seatalk://user?id={user_id}"/>')
        return ' '.join(mentions)
    
    def _build_message(self, timestamp: str, overbreak_count: str, 
                       ops_id_1: str, ops_id_2: str) -> str:
        """Build the formatted message for SeaTalk."""
        mentions = self._format_mentions(self.cc_user_ids)
        
        message = f"""**Inbound Overbreak Monitoring**
as of {timestamp}

>1 HR = {overbreak_count}
**Ops _id list of Overbreak**
{ops_id_1} - {ops_id_2}

cc: {mentions}"""
        return message

    def _get_range_lines(self, range_name: str) -> List[str]:
        """Return non-empty cell values from a sheet range as lines."""
        values = self.sheets_client.get_values(range_name)
        lines = []
        if not values:
            return lines

        for row in values:
            for cell in row:
                cell_value = cell.strip() if cell else ""
                if cell_value:
                    lines.append(cell_value)
        return lines

    def _build_range_message(self, title: str, range_name: str) -> str:
        """Build a bold-title message from a single-column range."""
        mentions = self._format_mentions(self.cc_user_ids)
        lines = self._get_range_lines(range_name)
        message = f"**{title}**"
        if lines:
            message += "\n" + "\n".join(lines)
        else:
            message += "\nNone"
        message += f"\n\ncc: {mentions}"
        return message

    def _get_target_group_ids(self) -> List[str]:
        """Get all target group IDs from group_id!A2:A, with env fallback."""
        if group_storage:
            group_storage.refresh()
            group_ids = group_storage.get_group_ids()
            if group_ids:
                return group_ids

        if self.group_id:
            return [self.group_id]
        return []

    def _send_messages_to_all_groups(self, messages: List[str]) -> bool:
        """Send every message to every configured group."""
        group_ids = self._get_target_group_ids()
        if not group_ids:
            logger.error("No group IDs found in group_id!A2:A or environment.")
            return False

        all_sent = True
        for group_id in group_ids:
            logger.info(f"Sending {len(messages)} message(s) to SeaTalk group {group_id}...")
            for message in messages:
                result = self.seatalk_client.send_text_message(
                    group_id,
                    message,
                    format_type=1
                )
                if not result:
                    logger.error(f"Failed to send alert to group {group_id}.")
                    all_sent = False
        return all_sent
    
    def _get_single_value(self, range_name: str, default: str = "") -> str:
        """Get a single cell value."""
        values = self.sheets_client.get_values(range_name)
        if values and len(values) > 0 and len(values[0]) > 0:
            return values[0][0]
        return default
    
    def check_and_process(self):
        """Check for new data and process if found."""
        logger.info("Checking for new data in workstation_dump...")
        
        has_data = self.sheets_client.is_range_not_empty(
            self.WORKSTATION_DUMP_RANGE
        )
        
        if has_data:
            logger.info("Data detected in workstation_dump! Processing...")
            self._process_new_data()
        else:
            logger.info("No data detected in workstation_dump.")
    
    def _process_new_data(self):
        """Process new data: add timestamp, wait, then send message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        success = self.sheets_client.update_value(
            self.TIMESTAMP_CELL, 
            timestamp
        )
        
        if not success:
            logger.error("Failed to update timestamp. Aborting.")
            return
        
        logger.info(f"Waiting {self.delay_seconds} seconds before sending message...")
        time.sleep(self.delay_seconds)
        
        overbreak_count = self._get_single_value(
            self.OVERBREAK_COUNT_CELL, 
            "N/A"
        )
        ops_id_1 = self._get_single_value(self.OPS_ID_CELL_1, "N/A")
        ops_id_2 = self._get_single_value(self.OPS_ID_CELL_2, "N/A")
        
        message = self._build_message(
            timestamp, 
            overbreak_count, 
            ops_id_1, 
            ops_id_2
        )
        messages = [message]

        no_breaktime_scan_message = self._build_range_message(
            "No Breaktime Scan in FMS Workstation",
            self.NO_BREAKTIME_SCAN_RANGE
        )
        messages.append(no_breaktime_scan_message)

        ongoing_breaktime_message = self._build_range_message(
            "Ongoing Breaktime",
            self.ONGOING_BREAKTIME_RANGE
        )
        messages.append(ongoing_breaktime_message)
        
        if self._send_messages_to_all_groups(messages):
            logger.info("Alerts sent successfully!")
        else:
            logger.error("One or more alerts failed to send.")


def run_scheduler():
    """Run the scheduled checks in a background thread."""
    interval = int(os.getenv('CHECK_INTERVAL_SECONDS', '30'))
    
    schedule.every(interval).seconds.do(lambda: monitor.check_and_process())
    
    logger.info(f"Scheduler started. Checking every {interval} seconds.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)


def is_valid_signature(signing_secret: str, body: bytes, signature: str) -> bool:
    """Verify SeaTalk webhook signature using SHA-256.
    
    Per Event Callback docs: hashlib.sha256(body + signing_secret).hexdigest()
    """
    if not signing_secret or not signature:
        return True  # Skip verification if not configured
    
    try:
        expected = hashlib.sha256(body + signing_secret.encode()).hexdigest()
        return expected == signature
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming SeaTalk webhooks with event verification and signature validation.
    
    Events handled:
    - event_verification: URL verification challenge
    - bot_added_to_group_chat: Store group info
    - bot_removed_from_group_chat: Remove group from storage
    - new_mentioned_message_received_from_group_chat: Handle mentions
    """
    body = request.get_data()
    signature = request.headers.get('signature', '')
    signing_secret = os.getenv('SEATALK_SIGNING_SECRET', '')
    
    # Log raw request for debugging
    logger.info(f"Received webhook. Signature: {signature[:20] if signature else 'None'}...")
    
    # 1. Validate signature if signing_secret is configured
    if signing_secret and not is_valid_signature(signing_secret, body, signature):
        logger.warning("Invalid webhook signature!")
        return jsonify({"error": "Invalid signature"}), 401
    
    # 2. Parse JSON body
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400
    
    event_type = data.get('event_type', '')
    event_id = data.get('event_id', '')
    
    logger.info(f"Processing event: {event_type} (ID: {event_id})")
    
    # 3. Handle event verification (URL verification)
    if event_type == EVENT_VERIFICATION:
        challenge = data.get('event', {}).get('seatalk_challenge', '')
        logger.info(f"Event verification received. Challenge: {challenge[:20]}...")
        # Return challenge for verification
        return jsonify({"seatalk_challenge": challenge}), 200
    
    # 4. Handle bot_added_to_group_chat
    elif event_type == BOT_ADDED_TO_GROUP_CHAT:
        event_data = data.get('event', {})
        group_info = event_data.get('group', {})
        group_name = group_info.get('group_name', 'Unknown')
        group_id = group_info.get('group_id', 'Unknown')
        inviter = event_data.get('inviter', {})
        
        logger.info(f"Bot added to group: {group_name} (ID: {group_id})")
        
        # Fetch full group info using Get Group Info API
        if monitor and group_id != 'Unknown':
            logger.info(f"Fetching full group info for {group_id}...")
            full_group_info = monitor.seatalk_client.get_group_info(group_id)
            
            if full_group_info and full_group_info.get('code') == 0:
                group_data = full_group_info.get('group', {})
                
                # Store group info
                storage_data = {
                    'group_id': group_id,
                    'group_name': group_data.get('group_name', group_name),
                    'group_settings': group_data.get('group_settings', {}),
                    'group_user_total': group_data.get('group_user_total', 0),
                    'group_bot_total': group_data.get('group_bot_total', 0),
                    'added_at': datetime.now().isoformat(),
                    'inviter': {
                        'seatalk_id': inviter.get('seatalk_id'),
                        'employee_code': inviter.get('employee_code'),
                        'email': inviter.get('email')
                    }
                }
                
                if group_storage:
                    group_storage.add_group(storage_data)
                    logger.info(f"Group {group_name} ({group_id}) stored successfully")
                    
                    # If this is the first group and no group_id is configured, use this one
                    if not monitor.group_id:
                        monitor.group_id = group_id
                        logger.info(f"Auto-configured group_id to {group_id}")
                else:
                    logger.error("GroupStorage not initialized!")
            else:
                # Store basic info if API call failed
                if group_storage:
                    storage_data = {
                        'group_id': group_id,
                        'group_name': group_name,
                        'added_at': datetime.now().isoformat(),
                        'inviter': inviter
                    }
                    group_storage.add_group(storage_data)
                    
                    if not monitor.group_id:
                        monitor.group_id = group_id
                        logger.info(f"Auto-configured group_id to {group_id} (using basic info)")
    
    # 5. Handle bot_removed_from_group_chat
    elif event_type == BOT_REMOVED_FROM_GROUP_CHAT:
        event_data = data.get('event', {})
        group_info = event_data.get('group', {})
        group_name = group_info.get('group_name', 'Unknown')
        group_id = group_info.get('group_id', 'Unknown')
        remover = event_data.get('remover', {})
        
        logger.info(f"Bot removed from group: {group_name} (ID: {group_id})")
        
        if group_storage and group_id != 'Unknown':
            group_storage.remove_group(group_id)
            
            # If this was the active group, clear it
            if monitor and monitor.group_id == group_id:
                # Try to use another group
                next_group = group_storage.get_primary_group_id()
                monitor.group_id = next_group
                if next_group:
                    logger.info(f"Switched to next available group: {next_group}")
                else:
                    logger.warning("No groups remaining. Bot cannot send messages.")
    
    # 6. Handle new_mentioned_message_received_from_group_chat
    elif event_type == NEW_MENTIONED_MESSAGE_RECEIVED_FROM_GROUP_CHAT:
        event_data = data.get('event', {})
        chat_info = event_data.get('chat', {})
        sender = event_data.get('sender', {})
        message = event_data.get('message', {})
        
        group_name = chat_info.get('group_name', 'Unknown')
        group_id = chat_info.get('group_id', 'Unknown')
        sender_name = sender.get('name', 'Unknown')
        message_text = message.get('text', {}).get('content', '')
        
        logger.info(f"Bot mentioned in {group_name} by {sender_name}: {message_text[:50]}...")
        
        # Could add auto-reply logic here
        # For now, just log it
    
    # 7. Handle new_bot_subscriber (1-on-1 chat started)
    elif event_type == NEW_BOT_SUBSCRIBER:
        event_data = data.get('event', {})
        subscriber = event_data.get('subscriber', {})
        user_name = subscriber.get('name', 'Unknown')
        seatalk_id = subscriber.get('seatalk_id', '')
        
        logger.info(f"New bot subscriber: {user_name} ({seatalk_id})")
    
    # 8. Handle message_from_bot_subscriber (message in 1-on-1 chat)
    elif event_type == MESSAGE_FROM_BOT_SUBSCRIBER:
        event_data = data.get('event', {})
        subscriber = event_data.get('subscriber', {})
        message = event_data.get('message', {})
        
        user_name = subscriber.get('name', 'Unknown')
        message_text = message.get('text', {}).get('content', '')
        
        logger.info(f"Message from {user_name}: {message_text[:50]}...")
    
    # 9. Handle interactive_message_click (button clicks)
    elif event_type == INTERACTIVE_MESSAGE_CLICK:
        event_data = data.get('event', {})
        user = event_data.get('user', {})
        callback_data = event_data.get('callback', '')
        
        user_name = user.get('name', 'Unknown')
        logger.info(f"Button click by {user_name}: {callback_data}")
    
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    # SeaTalk requires HTTP 200 response within 5 seconds
    return jsonify({"code": 0}), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/trigger-check', methods=['POST'])
def manual_trigger():
    """Manually trigger a check."""
    if monitor:
        monitor.check_and_process()
        return jsonify({"status": "check triggered"}), 200
    return jsonify({"error": "Monitor not initialized"}), 500


@app.route('/send-test-message', methods=['POST'])
def send_test_message():
    """Send a test message to the group."""
    if not monitor:
        return jsonify({"error": "Monitor not initialized"}), 500
    
    # Get group_id from request or use configured group
    group_id = request.json.get('group_id', monitor.group_id)
    if not group_id:
        return jsonify({"error": "No group_id configured or provided"}), 400
    
    test_message = request.json.get('message', 'Test message from Overbreak Bot')
    result = monitor.seatalk_client.send_text_message(
        group_id,
        test_message
    )
    
    if result:
        return jsonify({"status": "Message sent", "group_id": group_id, "result": result}), 200
    return jsonify({"error": "Failed to send message"}), 500


@app.route('/groups', methods=['GET'])
def list_groups():
    """List all stored groups."""
    if group_storage:
        groups = group_storage.get_all_groups()
        return jsonify({"groups": groups, "count": len(groups)}), 200
    return jsonify({"error": "GroupStorage not initialized"}), 500


# Initialize on first request (for gunicorn/production)
@app.before_request
def initialize_on_first_request():
    """Lazy initialization for gunicorn workers."""
    global monitor, group_storage, scheduler_running
    if monitor is None or group_storage is None:
        logger.info("Lazy initializing monitor and group_storage...")
        init_monitor()
    
    # Start scheduler only once
    if not scheduler_running:
        logger.info("Starting scheduler thread...")
        scheduler_running = True
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()


def main():
    """Main entry point."""
    global scheduler_running
    
    init_monitor()
    
    if not scheduler_running:
        scheduler_running = True
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()

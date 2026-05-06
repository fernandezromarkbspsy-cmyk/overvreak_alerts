#!/usr/bin/env python3
"""
Fetch and save group information from the running bot server.
Run this to create a local backup of stored group IDs.
"""

import json
import sys
import urllib.request
from urllib.error import HTTPError, URLError


def fetch_groups(server_url: str = "https://overbreak-alerts.onrender.com") -> dict:
    """Fetch groups from the bot server."""
    url = f"{server_url}/groups"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def save_groups(data: dict, filename: str = "groups_backup.json") -> bool:
    """Save groups to a local file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Groups saved to: {filename}")
        return True
    except Exception as e:
        print(f"Failed to save: {e}")
        return False


def print_group_summary(data: dict):
    """Print a summary of groups."""
    if not data or 'groups' not in data:
        print("No groups data found")
        return
    
    groups = data.get('groups', [])
    count = data.get('count', 0)
    
    print(f"\n{'='*50}")
    print(f"Total Groups: {count}")
    print(f"{'='*50}")
    
    for i, group in enumerate(groups, 1):
        print(f"\n[{i}] Group ID: {group.get('group_id')}")
        print(f"    Name: {group.get('group_name', 'N/A')}")
        print(f"    Added: {group.get('added_at', 'N/A')}")
        print(f"    Users: {len(group.get('users', []))}")
        print(f"    Bots: {len(group.get('bots', []))}")


def main():
    """Main entry point."""
    # Allow custom URL from command line
    server_url = sys.argv[1] if len(sys.argv) > 1 else "https://overbreak-alerts.onrender.com"
    
    print(f"Fetching groups from: {server_url}")
    
    data = fetch_groups(server_url)
    
    if data:
        print_group_summary(data)
        
        # Save to backup file
        save_groups(data, "groupid_backup.json")
        
        # Also save simplified version with just IDs
        simplified = {
            "group_ids": [g.get('group_id') for g in data.get('groups', [])],
            "count": data.get('count', 0)
        }
        save_groups(simplified, "group_ids.json")
        
        print(f"\n{'='*50}")
        print("For .env file, add:")
        for group in data.get('groups', []):
            print(f"SEATALK_GROUP_ID={group.get('group_id')}")
    else:
        print("Failed to fetch groups")
        sys.exit(1)


if __name__ == "__main__":
    main()

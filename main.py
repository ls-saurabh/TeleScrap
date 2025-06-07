from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, InputPeerChannel
from telethon.tl.types import UserStatusRecently, UserStatusLastMonth, UserStatusLastWeek
import csv
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Your credentials
api_id = 1234        # Replace with your API ID
api_hash = 'xxxxxxxxxxxxxxxxx'  # Replace with your API Hash
phone = '+91xxxxxxxx'       # Your phone number with country code

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, InputPeerChannel
from telethon.tl.types import (
    UserStatusRecently, UserStatusLastMonth, UserStatusLastWeek,
    UserStatusOffline, UserStatusOnline
)
import csv
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Your credentials
api_id = 13463176        # Replace with your API ID
api_hash = '9253cdb15bcfda6ad4556d651b1bfb10'  # Replace with your API Hash
phone = '+919651530574'       # Your phone number

def get_user_status(user):
    """Return user status as string"""
    if not user.status:
        return "Long time ago"
    if isinstance(user.status, UserStatusOnline):
        return "Online now"
    if isinstance(user.status, UserStatusRecently):
        return "Recently"
    if isinstance(user.status, UserStatusLastWeek):
        return "Within week"
    if isinstance(user.status, UserStatusLastMonth):
        return "Within month"
    if isinstance(user.status, UserStatusOffline):
        return "Offline"
    return "Long time ago"

def get_last_seen_date(user):
    """Get last seen timestamp if available"""
    if isinstance(user.status, UserStatusOffline):
        return user.status.was_online
    return None

def get_human_readable_date(timestamp):
    """Convert timestamp to readable date"""
    if not timestamp:
        return "N/A"
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

try:
    with TelegramClient(phone, api_id, api_hash) as client:
        if not client.is_user_authorized():
            logging.info("Initiating authorization...")
            client.send_code_request(phone)
            client.sign_in(phone, input('Enter the code: '))
            logging.info("Authorization successful")

        logging.info("Fetching your chats...")
        groups = []
        for dialog in client.iter_dialogs():
            if dialog.is_group:
                if hasattr(dialog.entity, 'title'):
                    groups.append(dialog.entity)
            elif dialog.is_channel:
                if getattr(dialog.entity, 'megagroup', False):
                    groups.append(dialog.entity)

        if not groups:
            logging.error("No groups found. Exiting.")
            exit()

        print("\nSelect a group to scrape:")
        for i, group in enumerate(groups):
            print(f"{i+1}. {group.title} (ID: {group.id})")

        selected = int(input("\nEnter choice number: ")) - 1
        if selected < 0 or selected >= len(groups):
            logging.error("Invalid selection")
            exit()

        target_group = groups[selected]
        logging.info(f"Selected group: {target_group.title}")

        # Get all participants with pagination
        all_participants = []
        offset = 0
        limit = 200
        total = 0

        if hasattr(target_group, 'access_hash'):
            peer = InputPeerChannel(target_group.id, target_group.access_hash)
        else:
            peer = target_group

        while True:
            participants = client(GetParticipantsRequest(
                channel=peer,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))
            if not participants.users:
                break
                
            all_participants.extend(participants.users)
            offset += len(participants.users)
            total += len(participants.users)
            logging.info(f"Fetched {total} participants...")
            
            if len(participants.users) < limit:
                break

        if not all_participants:
            logging.error("No participants found")
            exit()

        # Create output directory if needed
        os.makedirs("exports", exist_ok=True)
        filename = f"exports/{target_group.title.replace(' ', '_')}_members.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "User ID", "Username", "First Name", "Last Name", "Phone",
                "Status", "Last Seen", "Bot", "Deleted", "Premium", "Scam",
                "Access Hash"
            ])
            
            for user in all_participants:
                last_seen = get_last_seen_date(user)
                writer.writerow([
                    user.id,
                    f"@{user.username}" if user.username else "",
                    user.first_name or "",
                    user.last_name or "",
                    user.phone or "",
                    get_user_status(user),
                    get_human_readable_date(last_seen),
                    user.bot,
                    user.deleted,
                    user.premium,
                    user.scam,
                    user.access_hash
                ])

        logging.info(f"\nSuccess! Saved {len(all_participants)} members to {filename}")

except Exception as e:
    logging.error(f"An error occurred: {str(e)}", exc_info=True)
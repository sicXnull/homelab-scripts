import os
import subprocess
from datetime import datetime, date
import requests
from pytz import timezone

# Discord webhook URL
webhook_url = 'https://discord.com/api/webhooks/<embed>'

# Directories to backup
source_directories = [
    '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support',
    '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml'
]

# Backup destination 
backup_dir = '/path/to/backup/location'

def send_discord_message(filename, success=True, error_output=None):
    """ Sends a Discord message. """
    headers = {
        "Content-Type": "application/json"
    }

    if success:
        now = datetime.now(timezone('US/Eastern')).strftime(
            "%m/%d/%Y %I:%M:%S %p %Z")
        embed_data = {
            "embeds": [{
                "title": "Plex Backup Complete",
                "thumbnail": {
                    "url": "https://i.imgur.com/HoiBO9c.png"
                },
                "fields": [{
                    "name": "Filename",
                    "value": filename
                }, {
                    "name": "Date",
                    "value": now
                }],
                "color": 12868102
            }]
        }
    else:
        embed_data = {
            "embeds": [{
                "title": "Plex Backup failed",
                "description": f'```{error_output}```',
                "color": 15158332
            }]
        }

    response = requests.post(webhook_url, headers=headers, json=embed_data)
    if response.status_code != 204:
        print(f"Failed to send Discord message: {response.text}")

# Keep the most recent 5 backups
def clean_up_backups(save_dir):
    existing_files = os.listdir(save_dir)

    filtered_files = [file for file in existing_files if file.startswith("plex-backup-") and file.endswith(".tar.gz")]

    filtered_files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)))

    if len(filtered_files) > 5:
        files_to_remove = filtered_files[:-5]
        for file in files_to_remove:
            file_path = os.path.join(save_dir, file)
            os.remove(file_path)

def backup_and_send_message():

    today = date.today().strftime('%Y-%m-%d')

    backup_filename = f"plex-backup-{today}.tar.gz"

    backup_command = f"tar -czvf {os.path.join(backup_dir, backup_filename)}"

    for directory in source_directories:
        backup_command += f' "{directory}"'

    try:
        subprocess.run(backup_command, shell=True, check=True)
        print(f"Backup created successfully: {os.path.join(backup_dir, backup_filename)}")

        clean_up_backups(backup_dir)

        send_discord_message(backup_filename, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e}")
        send_discord_message(backup_filename, success=False, error_output=str(e))

if __name__ == "__main__":
    backup_and_send_message()

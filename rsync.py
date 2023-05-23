import json
import os
import requests
import re
import time
import subprocess
from datetime import datetime
import pytz

script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "rsync.log")

source_dirs = ["/opt", "/home"]
target_dir = "/NAS"
webhook_url = 'https://discord.com/api/webhooks/<embed>'

start_time = time.time()
hostname = os.uname()[1]
source_dirs_string = " ".join(source_dirs)

# Create the rsync.log file if it doesn't exist
if not os.path.exists(log_file_path):
    with open(log_file_path, "w") as log_file:
        pass

with open(log_file_path, "a") as log_file:
    result = subprocess.run(
        f"rsync -rltvz -a --no-links --no-specials --no-devices --no-inc-recursive --delete --stats --info=progress2 --verbose {source_dirs_string} {target_dir}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,

    )
    output = result.stdout.decode()
    log_file.write(output)

match = re.search(
    r"Number of files: ([\d,]+).*Number of created files: ([\d,]+).*Number of deleted files: ([\d,]+).*Number of regular files transferred: ([\d,]+).*",
    output, re.DOTALL)
if match:
    synced = match.group(1)
    created = match.group(2)
    deleted = match.group(3)
    transferred = match.group(4)
else:
    synced = 0
    created = 0
    deleted = 0
    transferred = 0

print(synced, created, deleted, transferred)

# Handle Error 23 (partial transfer) as success
if result.returncode == 23:
    result.returncode = 0

if result.returncode == 0:
    duration_seconds = time.time() - start_time
    duration_minutes, duration_seconds = divmod(duration_seconds, 60)
    duration_seconds = round(duration_seconds, 0)

    tz = pytz.timezone("America/New_York")

    embed = {
        'title': "hostname",
        "thumbnail": {
            "url": "https://i.imgur.com/dFqM7CG.png"
        },
        'fields': [
            {
                'name': 'Sync',
                'value': synced,
                'inline': True
            },
            {
                'name': 'Transfer',
                'value': "transferred",
                'inline': True
            },
            {
                'name': 'Delete',
                'value': deleted,
                'inline': True
            },
            {
                'name': 'Duration',
                'value': f'{int(duration_minutes)} minutes {int(duration_seconds)} seconds',
            },
            {
                'name': 'Date and Time',
                'value': datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M %p %Z'),
            },
        ],
        'color': 12868102
    }
else:
    with open(log_file_path, "r") as file:
        error_output = file.read()
        error_output = error_output[-2000:]
        embed = {
            'title': f'{hostname} rsync failed',
            'description': f'```{error_output}```',
            'color': 15158332
        }

# Send the message to discord
requests.post(webhook_url, json={'embeds': [embed]})

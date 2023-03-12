import requests
import subprocess
import re

# Discord webhook URL
webhook_url = "https://discord.com/api/webhooks/<embed>>"

# Discord embed message
def send_discord_message(expiration_date):
    embed = {
        "title": "Certificate Renewed",
        "description": f"Certificate for {base_domain} has been renewed",
        "color": 3066993,
        "fields": [
            {
                "name": "Expiration Date",
                "value": expiration_date
            }
        ],
        "thumbnail": {
            "url": "https://i.imgur.com/aj1M1iz.png"
        }
    }
    requests.post(webhook_url, json={'embeds': [embed]})

# Get current expiration date

subdomain = ""
base_domain = "whatever.com"
if subdomain:
    url = f'https://{subdomain}.{base_domain}'
else:
    url = f'https://{base_domain}'
output = subprocess.check_output(['curl', url, '-vI', '--stderr', '-']).decode()
expiration_date = re.search('expire date: (.*)', output).group(1)
print(expiration_date)

# Read previous expiration date from file
try:
    with open('expiration_date.txt', 'r') as file:
        previous_expiration_date = file.read()
except FileNotFoundError:
    previous_expiration_date = ''

# Compare expiration dates
if expiration_date != previous_expiration_date:
    # Send Discord message
    send_discord_message(expiration_date)
    # Save new expiration date
    with open('expiration_date.txt', 'w') as file:
        file.write(expiration_date)

import requests
import subprocess
import re
from datetime import datetime, timedelta


# Discord webhook URL
webhook_url = "https://discord.com/api/webhooks/<embed>>"

# Discord embed message
def send_discord_message(title, description, expiration_date):
    if title == "Certificate Renewed":
        color = 3066993  # Green
    elif title == "Certificate Expiring Soon":
        color = 15844367  # Yellow
    else:
        title = "Certificate Expired!"
        color = 15158332  # Red

    embed = {
        "title": title,
        "description": description,
        "color": color,
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
    json = {'embeds': [embed]}
    response = requests.post(webhook_url, json=json)
    print(response.status_code)
    print(response.content)


# Check if certificate is expiring soon or has expired and send notification
def check_certificate_expiry(expiration_date):
    expiry_datetime = datetime.strptime(expiration_date, "%b %d %H:%M:%S %Y %Z")
    warning_period = timedelta(days=15)  # Notify if certificate expires within 15 days
    if expiry_datetime - datetime.now() <= timedelta(0):
        send_discord_message("Certificate Expired", f"Wildcard certificate for {base_domain} has expired.", expiration_date)
    elif expiry_datetime - datetime.now() <= warning_period:
        send_discord_message("Certificate Expiring Soon", f"Wildcard certificate for {base_domain} will expire on {expiration_date}.", expiration_date)
    else:
        send_discord_message("Certificate Renewed", f"Wildcard certificate for {base_domain} has been renewed.", expiration_date)


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

# Compare expiration dates and send notification if necessary
if expiration_date != previous_expiration_date:
    check_certificate_expiry(expiration_date)
    # Save new expiration date
    with open('expiration_date.txt', 'w') as file:
        file.write(expiration_date)

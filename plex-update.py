import json
import requests
import subprocess
import re

webhook_url = 'https://discord.com/api/webhooks/<embed>'

result = subprocess.run(["dpkg-query", "-W", "plexmediaserver"], stdout=subprocess.PIPE)
output = result.stdout.decode("utf-8").strip()
try:
    current_version = re.search(r"\d+\.\d+\.\d+\.\d+-\w+", output).group()
    print(current_version)
except:
    print("Couldn't determine the current version of the Plex server")
    current_version = ""

# Get the newest version from https://plex.tv/pms/downloads/5.json
response = requests.get("https://plex.tv/pms/downloads/5.json")
newest_version_data = json.loads(response.text)["computer"]["Linux"]["releases"]

# Find the url for Intel/AMD 64-bit
url = None
for item in newest_version_data:
    if item["build"] == "linux-x86_64":
        url = item["url"]
        break

# Download and install the newest version if it's different from the current version
newest_version = url.split("/")[-1].split("_")[1]
if newest_version != current_version:
    subprocess.run(["wget", url])
    subprocess.run(["sudo", "dpkg", "-i", url.split("/")[-1]])

    # Send to Discord
    headers = {
      "Content-Type": "application/json",
    }
    payload = {
        "embeds": [
            {
                "title": "Plex Media Server",
                "description": "Plex Has Been Updated",
                "thumbnail": {
                    "url": "https://i.imgur.com/HoiBO9c.png"
                },
                "fields": [
                    {
                        "name": "Old Version",
                        "value": current_version,
                    },
                    {
                        "name": "New Version",
                        "value": newest_version,
                    },
                ],
                "color": 15048717,
            },
        ],
    }
    requests.post(webhook_url, headers=headers, json=payload)
else:
    print("You are running the latest version of the Plex server ({})".format(current_version))

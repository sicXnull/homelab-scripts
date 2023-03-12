import subprocess
import datetime
import requests
import os
import pytz
from pytz import timezone


webhook_url = 'https://discord.com/api/webhooks/<embed>'

hostname = os.uname()[1]
start_time = datetime.datetime.now(pytz.timezone('US/Eastern'))

subprocess.run(["sudo", "apt", "update", "-y"])

# Count the number of upgradable packages
output = subprocess.Popen(["apt", "list", "--upgradable"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = output.communicate()
output = stdout.decode('utf-8')
upgraded_packages = len([line for line in output.split('\n') if "upgradable" in line])

os.environ["DEBIAN_FRONTEND"] = "noninteractive"
subprocess.run(["sudo", "-E", "apt-get", "-o", "Dpkg::Options::=--force-confold", "-o", "Dpkg::Options::=--force-confdef", "dist-upgrade", "-q", "-y", "--allow-downgrades", "--allow-remove-essential", "--allow-change-held-packages"])
subprocess.run(["sudo", "apt-get", "autoclean", "-y"])

end_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
duration = end_time - start_time
duration_string = '{:02d}:{:02d}:{:02d}'.format(duration.seconds // 3600, (duration.seconds % 3600) // 60, duration.seconds % 60)

embed = {
    "title": hostname,
    "color": 14501908,
    "thumbnail": {
        "url": "https://i.imgur.com/4ygriPa.png"
    },
    "fields": [
        {
            'name': 'Package Updates',
            'value': upgraded_packages,
            'inline': True
        },
        {
            'name': 'Duration',
            'value': duration_string,
            'inline': True
        },
        {
            'name': 'Date and Time',
            'value': start_time.strftime('%Y-%m-%d %I:%M %p %Z'),
        },
    ],
}

response = requests.post(webhook_url, json={'embeds': [embed]})

print(response.status_code)

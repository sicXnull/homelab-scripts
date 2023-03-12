import requests
import os
import json
from dotenv import load_dotenv
from lxml import html
from os import path, makedirs, stat, listdir, remove
from datetime import datetime
from lxml.html import fromstring
from pytz import timezone

webhook_url = 'https://discord.com/api/webhooks/<embed>'

class PfBak:

    def __init__(self, pfhost, username, password, encrypted_pass, backup_dir, backup_data, backup_count, ssl, backup_rrd, backup_pkg):
        self.pfhost = pfhost
        self.username = username
        self.password = password
        self.encrypted_pass = encrypted_pass
        self.backup_dir = backup_dir if backup_dir else 'backups'
        self.backup_count = int(backup_count) if backup_count else 7
        self.ssl = ssl
        self.backup_rrd = backup_rrd
        self.backup_pkg = backup_pkg
        self.backup_data = backup_data
        self.verbose = True if os.getenv('VERBOSE') == "1" else False
        self.verify = False if ssl == "0" else True
        self.host = f"http://{pfhost}/" if ssl == "0" else f"https://{pfhost}/"
        self.session = requests.session()
        self.backup_name = f"config-{pfhost}-{datetime.now().strftime('%m-%d-%Y')}.xml"

        if self.verbose:
            print(self.host)

        if not path.exists(self.backup_dir):
            makedirs(self.backup_dir)

    def executeProcess(self):
        self.get_csrf()
        self.login()
        self.get_csrf(exist=True)
        self.get_config()
        self.delete_old_configs()

    def get_csrf(self, exist=False):
        if not exist:
            if self.verbose:
                print('Retrieving the "magic" CSRF Token.')
            r = self.session.get(f"{self.host}index.php", verify=self.verify)
            try:
                self.magic_csrf_token = html.fromstring(r.text).xpath('//input[@name=\'__csrf_magic\']/@value')[0]
            except:
                self.magic_csrf_token = ""
            if self.verbose:
                print(f'Token: {self.magic_csrf_token}')
        else:
            self.magic_csrf_token = html.fromstring(self.resp.text).xpath('//input[@name=\'__csrf_magic\']/@value')[0]
            if html.fromstring(self.resp.text).xpath('//title/text()')[0].startswith("Login"):
                exit("Login was not successful!")

    def login(self):
        if self.verbose:
            print(f'Logging in to {self.host}')
        data = {
            "__csrf_magic": self.magic_csrf_token,
            "usernamefld": self.username,
            "passwordfld": self.password,
            "login": "Login"
        }
        self.resp = self.session.post(f"{self.host}index.php", data=data, verify=self.verify)

    def get_config(self):
        if self.verbose:
            print('Retrieving the Configuration File')
            print(self.magic_csrf_token)

        data = {
            "__csrf_magic": self.magic_csrf_token,
            "download": "Download configuration as XML"
        }
        if self.encrypted_pass:
            data["encrypt"] = "yes"
            data["encrypt_password"] = self.encrypted_pass
            data["encrypt_password_confirm"] = self.encrypted_pass

        if not self.backup_rrd:
            data['donotbackuprrd'] = "yes"

        if not self.backup_pkg:
            data['nopackages'] = "yes"

        if self.backup_data:
            data["backupdata"] = "yes"

        pfresponse = self.session.post(f"{self.host}diag_backup.php",
                                     data=data,
                                     verify=self.verify)

        if not self.encrypted_pass:
            if len(fromstring(pfresponse.text).xpath('//pfsense')) != 1:
                exit("Something went wrong! The returned content was not a PfSense Configuration File!")

        else:
            if "config.xml" not in pfresponse.text:
                exit("Something went wrong! The returned content was not a PfSense Configuration File!")

        if self.verbose:
            print(f'Saving the Configuration to: {self.backup_dir}/{self.backup_name}')

        with open(f"{self.backup_dir}/{self.backup_name}", "w") as file:
            file.write(pfresponse.text)

        if self.verbose:
            print(f'Configuration saved.')

    def delete_old_configs(self):
        if self.verbose:
            print(f'Deleting old backups. Only saving newest {self.backup_count} configs.')
        file_times = []
        for filename in listdir(self.backup_dir):
            file_time = stat(path.join(self.backup_dir, filename)).st_mtime
            file_times.append((filename, file_time))
        file_times.sort(key=lambda x: x[1], reverse=True)
        for filename, file_time in file_times[self.backup_count:]:
            if self.verbose:
                print(f'Deleting Config: {self.backup_dir}/{filename}')
            remove(f'{self.backup_dir}/{filename}')



def send_discord_embed(filename, completion_time, success=True):
    if success:
        embed_data = {
            "embeds": [{
                "title": "pfSense Backup Complete",
                "thumbnail": {
                    "url": "https://i.imgur.com/XK0ILmE.png"
                },
                "fields": [{
                    "name": "Filename",
                    "value": filename
                }, {
                    "name": "Date",
                    "value": completion_time
                }],
                "color": 3066993
            }]
        }
    else:
        embed_data = {
            "embeds": [{
                "title": "pfSense Backup failed",
                "description": f'```{error_output}```',
                "color": 15158332
            }]
        }
    response = requests.post(webhook_url, data=json.dumps(embed_data), headers={"Content-Type": "application/json"})

if __name__ == "__main__":
    try:
        load_dotenv()
        pfhost = os.environ.get('PFHOST')
        username = os.environ.get('USERNAME')
        password = os.environ.get('PASSWORD')
        encrypted_pass = os.environ.get('ENCRYPTED_PASS')
        backup_rrd = os.environ.get('BACKUP_RRD')
        backup_pkg = os.environ.get('BACKUP_PKG')
        backup_count = os.environ.get('BACKUP_COUNT')
        backup_dir = os.environ.get('BACKUP_DIR')
        backup_data = os.getenv('BACKUP_DATA')
        ssl = os.environ.get('SSL')
        verbose = os.environ.get('VERBOSE')

        backup = PfBak(pfhost, username, password, encrypted_pass, backup_dir, backup_data, backup_count, ssl, backup_rrd, backup_pkg)
        backup.executeProcess()
        filename = backup.backup_name
        eastern = timezone('US/Eastern')
        completion_time = datetime.now(eastern).strftime("%m/%d/%Y %I:%M:%S %p %Z")
        send_discord_embed(filename, completion_time)
    except Exception as e:
        error_output = str(e)
        send_discord_embed(None, None, success=False)
        print(f"Backup failed: {e}")
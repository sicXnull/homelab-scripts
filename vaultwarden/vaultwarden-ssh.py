import os
import tarfile
from shutil import copytree, ignore_patterns, make_archive, move, rmtreee
from pathlib import Path
import sqlite3
from datetime import datetime
from tqdm import tqdm
from pytz import timezone
import requests
import configparser
import paramiko

webhook_url = "https://discord.com/api/webhooks/<embed>"

# Read the password from warden.ini file
config = configparser.ConfigParser()
config.read('/root/.secrets/warden.ini')
password = config['Vaultwarden']['password']

class Backup:
    def __init__(self,
                 datadir="/opt/bitwarden",
                 debug=True):

        self.now = datetime.now().strftime("%m-%d-%Y")

        self.debug = debug
        self.datadir = Path(datadir)
        self.stagedir = None

    def make_staging(self):
        """ Create the staging directory in /tmp. """
        self.stagedir = Path("/tmp") / f"backup-{self.now}"
        if self.stagedir.exists():
            if self.debug:
                print(f"Removing existing staging {self.stagedir}.")
            rmtree(self.stagedir, ignore_errors=False)
        if self.debug:
            print(f"Making staging {self.stagedir}")
        self.stagedir.mkdir(parents=True)

    def cleanup_staging(self):
        """ Remove the staging directory if it exists. """
        if self.stagedir is not None and self.stagedir.exists():
            if self.debug:
                print(f"Remove staging {self.stagedir}.")
            rmtree(self.stagedir, ignore_errors=False)

    def backup_db(self):
        """ Make a backup of the sqlite3 database separately, using the iterdump() method for database backups. """

        data_dbfile = self.datadir / "db.sqlite3"
        backup_dbfile = self.stagedir / "db.sqlite3"

        timeout_seconds = 30  # Adjust the timeout value as needed

        with sqlite3.connect(str(data_dbfile), timeout=timeout_seconds) as con, \
                sqlite3.connect(str(backup_dbfile), timeout=timeout_seconds) as backup_con:
            dump_gen = con.iterdump()
            dump_gen_list = list(dump_gen)
            total_commands = len(dump_gen_list)

            with tqdm(total=total_commands, desc="Backing up database", unit=" commands") as progress_bar:
                for command in dump_gen_list:
                    if command.strip().lower() != "commit;":
                        with backup_con:
                            backup_con.executescript(command)
                    progress_bar.update(1)

    def backup_everything_else(self):
        """ Using copytree(), we make a copy of all things except the database and the staging directory. """
        if self.debug:
            print(f"Copy files from {self.datadir} to {self.stagedir}.")
        copytree(self.datadir, self.stagedir, dirs_exist_ok=True, ignore=ignore_patterns('db.sqlite3*', 'staging'))

    def get_backup_filename(self):
        return f"backup-vaultwarden-{self.now}.tar.bz2"

    def backup_bztar(self):
        """ Compress the staging directory into a .tar.bz2 and move to backupdir. """
        if self.debug:
            print(f"Archive {self.stagedir} into {self.stagedir}.tar.bz2.")

        tar_filename = f"{self.stagedir.parent}/{self.stagedir.name}.tar.bz2"
        make_archive(str(self.stagedir.parent / self.stagedir.name), "bztar", self.stagedir)
        move(tar_filename, self.stagedir / self.get_backup_filename())  # Use get_backup_filename method

    def send_backup_via_ssh(self, backup_file_path, remote_host, remote_username, remote_private_key_path, remote_path):
        private_key = paramiko.RSAKey(filename=remote_private_key_path)
        transport = paramiko.Transport((remote_host, 22))
        transport.connect(username=remote_username, pkey=private_key)

        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_file_path = remote_path + "/" + backup_file_path.name

        try:
            sftp.put(str(backup_file_path), remote_file_path)
            print(f"Backup file {backup_file_path.name} sent to {remote_host}:{remote_file_path}")
        except Exception as e:
            print(f"Failed to send backup file: {e}")
        finally:
            sftp.close()
            transport.close()

    def send_discord_message(self, filename, success=True, error_output=None):
        """ Sends a Discord message via webhook with information about the backup. """
        headers = {
            "Content-Type": "application/json"
        }

        if success:
            now = datetime.now(timezone('US/Eastern')).strftime(
                "%m/%d/%Y %I:%M:%S %p %Z")
            embed_data = {
                "embeds": [{
                    "title": "Vaultwarden Backup Complete",
                    "thumbnail": {
                        "url": "https://i.imgur.com/2z5s0UP.png"
                    },
                    "fields": [{
                        "name": "Filename",
                        "value": filename
                    }, {
                        "name": "Date",
                        "value": now
                    }],
                    "color": 3066993
                }]
            }
        else:
            embed_data = {
                "embeds": [{
                    "title": "Vaultwarden Backup failed",
                    "description": f'```{error_output}```',
                    "color": 15158332
                }]
            }

        response = requests.post(webhook_url, headers=headers, json=embed_data)
        if response.status_code != 204:
            print(f"Failed to send Discord message: {response.text}")

    def backup(self):
        try:
            self.make_staging()
            self.backup_everything_else()
            self.backup_db()
            self.backup_bztar()

            # Encrypt the tar file
            tar_file = self.stagedir / self.get_backup_filename()
            encrypted_tar_file = tar_file.with_suffix('.tar.bz2.enc')
            os.system(f'7z a -p{password} -y {encrypted_tar_file} {tar_file}')
            os.remove(tar_file)

            # Transfer the encrypted tar file via SSH
            remote_private_key_path = "/home/<USER>/.ssh/id_rsa"  # Replace with the path to your private key
            backup_file = encrypted_tar_file
            self.send_backup_via_ssh(
                backup_file,
                remote_host="<IP ADDRESS",
                remote_username="<USER>",
                remote_private_key_path=remote_private_key_path,
                remote_path="/path/to/Vaultwarden"
            )

            # Send Discord webhook notification
            self.send_discord_message(encrypted_tar_file.name)

            self.cleanup_staging()
        except Exception as e:
            error_output = str(e)
            self.send_discord_message(None, success=False, error_output=error_output)
            raise

    def expire(self, max_backups=5):
        """ Expire Backups older than the most recent max_backups (default: 5). """
        backup_files = list(self.stagedir.glob("*.tar.bz2.enc"))
        backup_files.sort(key=lambda p: p.stat().st_ctime, reverse=True)

        for idx, p in enumerate(backup_files):
            if idx >= max_backups:
                if self.debug:
                    print(f"Expire file {p} (index: {idx}).")
                p.unlink()
            else:
                if self.debug:
                    print(f"File {p} still good (index: {idx}).")


b = Backup()
b.backup()
b.expire()

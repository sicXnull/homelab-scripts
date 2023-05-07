#! /usr/bin/env python3

from pathlib import Path
from datetime import datetime
import requests
from pytz import timezone
import sqlite3
from tqdm import tqdm
from shutil import copytree, ignore_patterns, make_archive, rmtree, move

webhook_url = 'https://discord.com/api/webhooks/<embed>'

class Backup:
    """
    Make a backup of a vaultwarden installation.

    We create a backups directory, in which we create a staging subdirectory.
    Files are copied into the stage, according to the instructions in
    https://github.com/dani-garcia/vaultwarden/wiki/Backing-up-your-vault.
    The stage is then archives into a .tar.bz2, and removed.
    """
    def __init__(self,
                 datadir="/path/to/vaultwarden",
                 backupdir="/path/to/backup/Vaultwarden",
                 debug=True):
        """ Constructor.
        datadir: Location of the vaultwarden installation. Must be readable to the program.
        backupdir: Location where the staging subdirectory will be created. Later the .tar.bz2 will be left here.
            The staging directory will be {backupdir}/backup-{now}.
        debug: prints some messages when set to True (Default: False).
        """
        self.now = datetime.now().strftime("%m-%d-%Y")

        self.debug = debug
        self.datadir = Path(datadir)
        self.backupdir = Path(backupdir)
        self.stagedir = None

    def make_staging(self):
        """ Create the staging directory in /tmp. """
        self.stagedir = Path("/tmp") / f"backup-{self.now}"
        if self.debug:
            print(f"Making staging {self.stagedir}")
        self.stagedir.mkdir(parents=True, exist_ok=False)

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
                    if command.strip().lower() != "commit;":  # Filter out the "COMMIT;" statement
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
        move(tar_filename, self.backupdir / self.get_backup_filename())

    def send_discord_message(self, filename, success=True, error_output=None):
        """ Sends a Discord message. """
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
            self.cleanup_staging()
            backup_file = self.backupdir / self.get_backup_filename()
            self.send_discord_message(backup_file.name)
        except Exception as e:
            error_output = str(e)
            self.send_discord_message(None, success=False, error_output=error_output)
            raise  # Re-raise the exception to show the error message in the console

    def expire(self, max_backups=5):
        """ Expire Backups older than the most recent max_backups (default: 5). """
        backup_files = list(self.backupdir.glob("*.tar.bz2"))
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

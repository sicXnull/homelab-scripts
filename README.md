
# Homelab Scripts w/Discord Embeds

Various scripts I use to maintain my homelab. Sends notifications to Discord




## Scripts


[apt-upgrade.py](https://github.com/sicXnull/homelab-scripts/blob/main/apt-upgrade.py) - Pretty straight forward. Runs apt-get update & upgrade. Sends notification when complete 
- change `webhook_url` &  `pytz.timezone` as needed <br><br>

![image](https://user-images.githubusercontent.com/31908995/224578518-0e2852ef-0f09-4a41-9a2a-3c7b18a576de.png)

[rsync.py](https://github.com/sicXnull/homelab-scripts/blob/main/rsync/rsync.py) - Runs `rsync` command. ignores the various filetypes that cause errors. Sends notification when complete 
- change `webhook_url` `source_dirs` `target_dir` & `pytz.timezone` <br><br>

[rsync-ssh.py](https://github.com/sicXnull/homelab-scripts/blob/main/rsync/rsync-ssh.py) - Runs `rsync` command - Syncs to remote machine via SSH ignores the various filetypes that cause errors. Sends notification when complete 
- change `private_key` `webhook_url` `source_dirs` `target_dir` & `pytz.timezone` <br><br>

![image](https://user-images.githubusercontent.com/31908995/224581849-abbdb49a-2d03-4f9c-b889-60dc07fdf87e.png)


[certbot-renewal.py](https://github.com/sicXnull/homelab-scripts/blob/main/certbot-renewal.py) - Checks expiration date of certificate. Notifies when renewed
- change `webhook_url` `subdomain` & `base_domain` (TO DO: Notify if cert expires, renew) <br><br>

![image](https://user-images.githubusercontent.com/31908995/224579506-46b69fc7-0ee5-4ea7-bcb1-a490c811fdde.png)


[plex-update.py](https://github.com/sicXnull/homelab-scripts/blob/main/plex-update.py) - checks current Plex version and updates if needed. Notifies when updated
- change `webhook_url` <br><br>

![image](https://user-images.githubusercontent.com/31908995/224579556-099df1b2-1ddc-4d04-82ae-6ae483808d05.png)


[pfbak.py](https://github.com/sicXnull/homelab-scripts/blob/main/pfsense-backup/pfbak.py) - creates pfSense backup and notified when complete
- change `.env` file <br><br>

![image](https://user-images.githubusercontent.com/31908995/224580012-31963672-0424-4aa6-89d0-e491540df247.png)

[vaultwarden.py](https://github.com/sicXnull/homelab-scripts/blob/main/vaultwarden/vaultwarden.py) - Modified version of an [existing VaultWarden backup script](https://github.com/isotopp/vaultwarden-backup). Added ability to save to samba share and send notifications. The existing VaultWarden DB is encrypted but still stores sensitive data in cleartext such as email address, password hint and websites. This encrypts the archive to add another layer of protection.

[vaultwarden-ssh.py](https://github.com/sicXnull/homelab-scripts/blob/main/vaultwarden/vaultwarden-ssh.py) - Same as above, sends to remote machine via SSH instead. Change `remote_host` , `remote_username`, `remote_path` as well as everything below

- change `webhook_url`
- create `.secrets` folder if it does not already exist `sudo mkdir /root/.secrets`
- add the following to warden.ini `sudo nano /root/.secrets/warden.ini`
```
[Vaultwarden]
password = YOUR_PASSWORD_HERE
```
- Set permissions so only root has access
```
sudo chmod 700 /root/.secrets
sudo chmod 600 /root/.secrets/warden.ini
sudo chown -R root:root /root/.secrets
```
<br>

![image](https://user-images.githubusercontent.com/31908995/236705386-efe51958-e6e3-474e-8e93-1b2c33bc81de.png)

[snapraid.py](https://github.com/sicXnull/homelab-scripts/blob/main/snapraid/snapraid.py) - fork of [snapraid-runner](https://github.com/Chronial/snapraid-runner) 
- change `webhook_url` in snapraid-runner.conf. otherwise follow same configuration.<br><br>

![image](https://github.com/sicXnull/homelab-scripts/assets/31908995/a0dbcf9f-d799-434e-a608-a46e253659cb)

## Deployment

Add to crontab. Example:

- rsync Daily @ 10pm

```
0 22 * * * python3 /opt/homelab-scripts/rsync.py
```

- SnapRaid Daily @ 1am
```
0 1 * * * python3 /opt/homelab-scripts/snapraid/snapraid.py -c /opt/homelab-scripts/snapraid/snapraid-runner.conf
```

- pfSense Sundays @ 8am
```
0 8 * * 0 python3 /opt/homelab-scripts/pfsense/pfbak.py
```

- Vaultwarden Sundays @ 8:05am
```
5 8 * * 0 python3 /opt/homelab-scripts/pfsense/vaultwarden.py
```
- apt-upgrade Sundays @ 9am

```
0 9 * * 0 python3 /opt/homelab-scripts/apt-upgrade.py
```

- Plex update Daily @ 4am
```
0 4 * * * python3 /opt/homelab-scripts/plex-update.py
```

- certbot renewal every 6 hours
```
0 */6 * * * python3 /opt/homelab-scripts/certbot-renewal.py
```

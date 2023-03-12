
# Homelab Scripts w/Discord Embeds

Various scripts I use to maintain my homelab. Sends notifications to Discord




## Scripts


[apt-upgrade.py](https://github.com/sicXnull/homelab-scripts/blob/main/apt-upgrade.py) - Pretty straight forward. Runs apt-get update & upgrade. Sends notification when complete 
- change `webhook_url` &  `pytz.timezone` as needed

[rsync.py](https://github.com/sicXnull/homelab-scripts/blob/main/rsync.py) - Runs `rsync` command. ignores the various filetypes that cause errors. Sends notification when complete 
- change `webhook_url` `source_dirs` `target_dir` & `pytz.timezone`

[certbot-renewal.py](https://github.com/sicXnull/homelab-scripts/blob/main/certbot-renewal.py) - Checks expiration date of certificate. Notifies when renewed
- change `webhook_url` `subdomain` & `base_domain`

[plex-update.py](https://github.com/sicXnull/homelab-scripts/blob/main/plex-update.py) - checks current Plex version and updates if needed. Notifies when updated
- change `webhook_url` `subdomain` & `base_domain`

[pfbak.py](https://github.com/sicXnull/homelab-scripts/blob/main/pfsense-backup/pfbak.py) - creates pfSense backup and notified when complete
- change `.env` file

[snapraid.py](https://github.com/sicXnull/homelab-scripts/blob/main/snapraid/snapraid.py) - fork of [snapraid-runner](https://github.com/Chronial/snapraid-runner) 
- change `webhook_url` in snapraid-runner.conf. otherwise follow same configuration. 


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

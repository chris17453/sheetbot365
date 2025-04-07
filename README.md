# Email Automation CLI Usage Examples with Config File

## Using the default config location
```bash
# The script will look for config in /etc/email_automation/config.ini by default
python email_automation.py scan
```

## Specifying a custom config file
```bash
python email_automation.py -c /path/to/my/config.ini scan
python email_automation.py --config /path/to/my/config.ini scan
```

## Scan for new emails (basic)
```bash
python email_automation.py -c config.ini scan
```

## Scan for new emails with auto-deletion of old processed emails
```bash
python email_automation.py -c config.ini scan --auto-mark-deleted --days-old 30
```

## Scan with higher limit (up to 100 emails)
```bash
python email_automation.py -c config.ini scan --limit 100
```

## Delete emails from database only (90+ days old)
```bash
python email_automation.py -c config.ini delete --days-old 90 --db-only
```

## Delete emails from email inbox only (60+ days old)
```bash
python email_automation.py -c config.ini delete --days-old 60 --email-only
```

## Delete emails from both database and email inbox (120+ days old)
```bash
python email_automation.py -c config.ini delete --days-old 120 --both
```

## Get status counts
```bash
python email_automation.py -c config.ini status
```

## Get detailed status information
```bash
python email_automation.py -c config.ini status --verbose
```

## Setting up as a cron job
Add these lines to your crontab (edit with `crontab -e`):

```
# Scan for new emails every hour
0 * * * * /usr/bin/python /path/to/email_automation.py -c /path/to/config.ini scan --auto-mark-deleted

# Delete old emails once a week (Sunday at 2am)
0 2 * * 0 /usr/bin/python /path/to/email_automation.py -c /path/to/config.ini delete --days-old 90 --both
```
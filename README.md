# Dynamic DNS Updater for Cloudflare

A lightweight, automated solution to keep your Cloudflare DNS records synchronized with your dynamic IP address. **Perfect for home labs, home servers, and self-hosted services.**

## What Does This Do?

If you're running services at home (web servers, game servers, home automation, NAS, etc.) and your ISP assigns you a dynamic IP address that changes periodically, this tool automatically updates your DNS records on Cloudflare whenever your IP changes. This ensures your domain always points to your current IP address.

### The Problem

Most residential internet connections have dynamic IP addresses that change unpredictably. When your IP changes, your DNS record becomes stale, and your services become unreachable via your domain name.

### The Solution

This program:
1. Checks your current external IP address
2. Compares it with your Cloudflare DNS record
3. Automatically updates the DNS record if they differ
4. Runs continuously, checking every 1 minute

## Home Lab Ready

**This project is designed specifically for home lab and personal use.** It's:
- ✅ Simple to configure and run
- ✅ Lightweight and efficient (perfect for running on a Raspberry Pi or spare server)
- ✅ Easy to modify and customize for your specific needs
- ✅ Open source - change anything you want!
- ✅ Well-documented for learning and experimentation

**Feel free to fork, modify, and adapt this to your needs!** Whether you want to:
- Change the check interval (currently 1 minute)
- Add support for multiple DNS records
- Integrate with other services
- Add notifications (email, Discord, Slack, etc.)
- Support other DNS providers

The code is straightforward and documented - hack away!

## Features

- 🔄 **Built-in Scheduler**: Automatically checks every 1 minute (no cron needed)
- 📊 **Advanced Logging**: Color-coded console output with file logging
- 🔒 **Secure**: Credentials stored in external JSON config (not in code)
- 🐳 **Docker Ready**: Run in a container with Docker Compose
- 💪 **Robust**: Continues running even if checks fail
- 🎨 **Visual**: Easy-to-read color-coded log levels
- 📁 **Organized**: Automatic log rotation and compression

## Quick Start

### Option 1: Run with Docker (Recommended)

1. **Clone and configure**:
   ```bash
   git clone <your-repo-url>
   cd dns_update
   mkdir config
   cp config.sample.json config/config.json
   # Edit config/config.json with your Cloudflare credentials
   ```

2. **Start the container**:
   ```bash
   cd docker
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f dns-updater
   ```

That's it! The container will now check your DNS every minute and update when needed.

### Option 2: Run with Python Directly

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure**:
   ```bash
   mkdir config
   cp config.sample.json config/config.json
   # Edit config/config.json with your credentials
   ```

3. **Run**:
   ```bash
   python dns_update.py
   ```

## Configuration

### Getting Your Cloudflare API Key

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Go to **My Profile** → **API Tokens**
3. Click **View** next to **Global API Key**
4. Copy your API key

### Configuration File (`config/config.json`)

```json
{
  "zone": "example.com",
  "dnsrecord": "home.example.com",
  "cloudflare_auth_email": "your-email@example.com",
  "cloudflare_auth_key": "your-cloudflare-api-key-here"
}
```

- **zone**: Your root domain (the zone in Cloudflare)
- **dnsrecord**: The full subdomain you want to update
- **cloudflare_auth_email**: Your Cloudflare account email
- **cloudflare_auth_key**: Your Cloudflare Global API Key

## Log Output

The Python script provides colorful, informative logs:

```
2025-01-15 10:30:00 | INFO     | Logging initialized
2025-01-15 10:30:00 | INFO     | DNS Update Scheduler started for home.example.com
2025-01-15 10:30:00 | INFO     | Running checks every 1 minute. Press Ctrl+C to stop.
2025-01-15 10:30:00 | INFO     | Starting DNS update check for home.example.com
2025-01-15 10:30:01 | INFO     | Current IP is 203.0.113.45
2025-01-15 10:30:02 | INFO     | Cloudflare IP is 203.0.113.45
2025-01-15 10:30:02 | SUCCESS  | home.example.com is currently set to 203.0.113.45; no changes needed
```

When an IP change is detected:
```
2025-01-15 11:45:00 | INFO     | Current IP is 203.0.113.99
2025-01-15 11:45:01 | INFO     | Cloudflare IP is 203.0.113.45
2025-01-15 11:45:01 | WARNING  | DNS record needs updating from 203.0.113.45 to 203.0.113.99
2025-01-15 11:45:02 | INFO     | Zone ID for example.com is abc123def456
2025-01-15 11:45:03 | INFO     | DNS record ID for home.example.com is xyz789
2025-01-15 11:45:04 | SUCCESS  | Successfully updated home.example.com to 203.0.113.99
```

## Docker Deployment

### Using Docker Compose (Easiest)

```bash
cd docker
docker-compose up -d          # Start in background
docker-compose logs -f        # View logs
docker-compose down           # Stop
docker-compose restart        # Restart
```

### Using Docker Directly

```bash
# Build
docker build -f docker/Dockerfile -t dns-updater .

# Run
docker run -d \
  --name dns-updater \
  --restart unless-stopped \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  dns-updater

# View logs
docker logs -f dns-updater
```

## Customization Ideas

Since this is designed for home lab use, here are some ideas for customization:

### Change Check Interval

Edit `dns_update.py` line 284:
```python
# Change from 1 minute to 5 minutes
schedule.every(5).minutes.do(check_and_update_dns)
```

### Add Email Notifications

Add this function:
```python
import smtplib
from email.message import EmailMessage

def send_notification(subject, message):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'dns-updater@example.com'
    msg['To'] = 'you@example.com'
    msg.set_content(message)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('your-email@gmail.com', 'your-app-password')
        smtp.send_message(msg)

# Call it when IP changes (line 254):
send_notification('DNS Updated', f'Updated {dnsrecord} to {current_ip}')
```

### Support Multiple DNS Records

Modify `config.json`:
```json
{
  "zone": "example.com",
  "dnsrecords": [
    "home.example.com",
    "vpn.example.com",
    "nas.example.com"
  ],
  "cloudflare_auth_email": "your-email@example.com",
  "cloudflare_auth_key": "your-cloudflare-api-key-here"
}
```

Then update the code to loop through `dnsrecords`.

### Add Discord/Slack Webhooks

```python
import requests

def notify_discord(message):
    webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK"
    requests.post(webhook_url, json={"content": message})

# Call when IP changes
notify_discord(f"🔄 DNS updated: {dnsrecord} → {current_ip}")
```

## Requirements

### Python
- Python 3.6+
- requests
- loguru
- schedule

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Docker
- Docker
- Docker Compose (optional but recommended)

## Project Structure

```
dns_update/
├── dns_update.py           # Main Python application
├── config.sample.json      # Sample configuration file
├── requirements.txt        # Python dependencies
├── config/                 # Your config files (git-ignored)
│   └── config.json
├── logs/                   # Log files (git-ignored)
│   └── dns_update_YYYY-MM-DD.log
├── docker/                 # Docker files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.md
├── CLAUDE.md              # Developer documentation
└── README.md              # This file
```

## Troubleshooting

### Script says "Configuration file not found"
Make sure you've created `config/config.json` based on `config.sample.json`.

### DNS not updating
1. Verify your Cloudflare credentials are correct
2. Check that the DNS record already exists in Cloudflare
3. Ensure the zone name matches your Cloudflare zone
4. Check logs for API error messages

### Docker container won't start
1. Ensure `config/config.json` exists
2. Check logs: `docker-compose logs dns-updater`
3. Verify JSON syntax in config file

### Can't reach services after IP update
DNS changes can take a few minutes to propagate. Most DNS resolvers respect TTL, which is set to automatic (TTL=1) in this script for fastest updates.

## Security Notes

- **Never commit `config.json`** with real credentials (it's git-ignored by default)
- Store your Cloudflare API key securely
- Consider using Cloudflare API tokens with limited scope instead of Global API Key
- The Docker setup mounts config as read-only for extra security

## Contributing

This is a home lab project - contributions, forks, and modifications are welcome! Feel free to:
- Open issues for bugs or suggestions
- Submit pull requests with improvements
- Fork and customize for your needs
- Share your modifications with the community

## License

This project is provided as-is for personal and home lab use. Modify and use as you see fit!

## Acknowledgments

- Built for home lab enthusiasts and self-hosters
- Designed to be simple, reliable, and hackable
- Inspired by the need for reliable DDNS solutions for home infrastructure

## Support

For questions or issues:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Consult `CLAUDE.md` for technical details
4. Open an issue on the repository

---

**Made for home labs, by home lab enthusiasts. Happy self-hosting! 🏠🔧**

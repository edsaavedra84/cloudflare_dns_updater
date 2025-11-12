#!/usr/bin/env python3

"""
A Python script to update a Cloudflare DNS A record with the external IP of the source machine.
Used to provide DDNS service for dynamic IP addresses.
Requires the DNS record to be pre-created on Cloudflare.
"""

import json
import sys
import time
import signal
import requests
import schedule
from pathlib import Path
from loguru import logger


def setup_logging():
    """Configure loguru to log to both console and file with colors"""
    # Remove default logger
    logger.remove()

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Add colorized console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    # Add file handler with rotation
    log_file = logs_dir / "dns_update_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip"  # Compress old logs
    )

    logger.info("Logging initialized")


def load_config(config_path="config/config.json"):
    """Load configuration from JSON file"""
    config_file = Path(config_path)

    if not config_file.exists():
        logger.error(f"Configuration file '{config_path}' not found")
        logger.info("Please create a config.json file with the required parameters")
        logger.info("See config.sample.json for an example")
        sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Validate required fields
        required_fields = ['zone', 'dnsrecord', 'cloudflare_auth_email', 'cloudflare_auth_key']
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            logger.error(f"Missing required fields in config: {', '.join(missing_fields)}")
            sys.exit(1)

        logger.debug(f"Configuration loaded successfully from {config_path}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def get_external_ip():
    """Get the current external IP address"""
    try:
        logger.debug("Fetching external IP address from checkip.amazonaws.com")
        response = requests.get("https://checkip.amazonaws.com", timeout=10)
        response.raise_for_status()
        ip = response.text.strip()
        logger.debug(f"External IP retrieved: {ip}")
        return ip
    except requests.RequestException as e:
        logger.error(f"Error getting external IP: {e}")
        raise


def get_cloudflare_dns_ip(dnsrecord):
    """Get the current IP from Cloudflare DNS using their API resolver"""
    try:
        logger.debug(f"Querying Cloudflare DNS for {dnsrecord}")
        response = requests.get(
            f"https://1.1.1.1/dns-query?name={dnsrecord}&type=A",
            headers={"Accept": "application/dns-json"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get('Answer'):
            ip = data['Answer'][0]['data']
            logger.debug(f"Cloudflare DNS returned: {ip}")
            return ip
        logger.debug(f"No DNS record found for {dnsrecord}")
        return None
    except requests.RequestException as e:
        logger.warning(f"Could not query DNS via Cloudflare API: {e}")
        return None


def get_zone_id(zone, auth_email, auth_key):
    """Get the Cloudflare zone ID for the given zone"""
    url = f"https://api.cloudflare.com/client/v4/zones?name={zone}&status=active"
    headers = {
        "X-Auth-Email": auth_email,
        "X-Auth-Key": auth_key,
        "Content-Type": "application/json"
    }

    try:
        logger.debug(f"Fetching zone ID for {zone}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            logger.error(f"Cloudflare API returned error: {data.get('errors')}")
            raise Exception(f"Cloudflare API error: {data.get('errors')}")

        if not data.get('result'):
            logger.error(f"Zone '{zone}' not found")
            raise Exception(f"Zone '{zone}' not found")

        zone_id = data['result'][0]['id']
        logger.debug(f"Zone ID for {zone}: {zone_id}")
        return zone_id
    except requests.RequestException as e:
        logger.error(f"Error getting zone ID: {e}")
        raise


def get_dns_record_id(zone_id, dnsrecord, auth_email, auth_key):
    """Get the DNS record ID for the given A record"""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={dnsrecord}"
    headers = {
        "X-Auth-Email": auth_email,
        "X-Auth-Key": auth_key,
        "Content-Type": "application/json"
    }

    try:
        logger.debug(f"Fetching DNS record ID for {dnsrecord}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            logger.error(f"Cloudflare API returned error: {data.get('errors')}")
            raise Exception(f"Cloudflare API error: {data.get('errors')}")

        if not data.get('result'):
            logger.error(f"DNS record '{dnsrecord}' not found")
            raise Exception(f"DNS record '{dnsrecord}' not found")

        record_id = data['result'][0]['id']
        logger.debug(f"DNS record ID for {dnsrecord}: {record_id}")
        return record_id
    except requests.RequestException as e:
        logger.error(f"Error getting DNS record ID: {e}")
        raise


def update_dns_record(zone_id, record_id, dnsrecord, ip, auth_email, auth_key):
    """Update the DNS A record with the new IP"""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        "X-Auth-Email": auth_email,
        "X-Auth-Key": auth_key,
        "Content-Type": "application/json"
    }
    payload = {
        "type": "A",
        "name": dnsrecord,
        "content": ip,
        "ttl": 1,
        "proxied": False
    }

    try:
        logger.debug(f"Updating DNS record {dnsrecord} to {ip}")
        response = requests.put(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            logger.error(f"Failed to update DNS record: {data.get('errors')}")
            raise Exception(f"Failed to update DNS record: {data.get('errors')}")

        logger.debug(f"DNS record updated successfully")
        return data
    except requests.RequestException as e:
        logger.error(f"Error updating DNS record: {e}")
        raise


# Global configuration storage
_config = None


def check_and_update_dns():
    """Check and update DNS record if needed"""
    global _config
    _config = load_config()

    zone = _config['zone']
    dnsrecord = _config['dnsrecord']
    auth_email = _config['cloudflare_auth_email']
    auth_key = _config['cloudflare_auth_key']

    logger.info(f"Starting DNS update check for {dnsrecord}")

    try:
        # Get current external IP
        current_ip = get_external_ip()
        logger.info(f"Current IP is {current_ip}")

        # Get current Cloudflare DNS IP
        cf_ip = get_cloudflare_dns_ip(dnsrecord)
        logger.info(f"Cloudflare IP is {cf_ip}")

        # Check if update is needed
        if cf_ip and cf_ip == current_ip:
            logger.success(f"{dnsrecord} is currently set to {current_ip}; no changes needed")
            return

        # Update is needed
        logger.warning(f"DNS record needs updating from {cf_ip} to {current_ip}")

        # Get zone ID
        zone_id = get_zone_id(zone, auth_email, auth_key)
        logger.info(f"Zone ID for {zone} is {zone_id}")

        # Get DNS record ID
        record_id = get_dns_record_id(zone_id, dnsrecord, auth_email, auth_key)
        logger.info(f"DNS record ID for {dnsrecord} is {record_id}")

        # Update the record
        result = update_dns_record(zone_id, record_id, dnsrecord, current_ip, auth_email, auth_key)
        logger.success(f"Successfully updated {dnsrecord} to {current_ip}")
        logger.debug(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        logger.error(f"Unexpected error during DNS update: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, exiting gracefully...")
    sys.exit(0)


def main():
    """Main function to setup and run the scheduler"""
    global _config

    # Setup logging
    setup_logging()

    # Load configuration
    _config = load_config()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"DNS Update Scheduler started for {_config['dnsrecord']}")
    logger.info("Running checks every 1 minute. Press Ctrl+C to stop.")

    # Schedule the job to run every 1 minute
    schedule.every(1).minutes.do(check_and_update_dns)

    # Run the job immediately on startup
    check_and_update_dns()

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()

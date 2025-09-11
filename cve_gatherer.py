#!/usr/bin/env python3

# Description : Gather latest CVEs from NIST.gov and send them to a discord webhook
# Author      : Meganuke_
# Date        : 2025-09-10
# Usage       : python3 cve_gatherer.py
# Notes       : TODO - Review the script to understand it's usage and align it to my needs

import requests
import json
from datetime import datetime, timedelta
import os

# Set up the webhook URL by fetching it from the .ENV variables 
DISCORD_WEBHOOK_URL = os.environ['CVE_GATHERER_WEBHOOK'] 

# NVD API endpoint for fetching vulnerabilities. We'll query for CVEs created in the last 24 hours.
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Set a user agent as per NVD API best practices.
HEADERS = {
    'User-Agent': 'CVE-Discord-Notifier-Script/0.2'
}

def fetch_latest_cves(hours=24):
    """
    Fetches CVEs created in the last N hours from the NVD API.

    Args:
        hours (int): The number of hours to look back for new CVEs.

    Returns:
        list: A list of CVE records, or an empty list on failure.
    """
    try:
        # Calculate the start and end dates for the query
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)

        # Format dates for the API request
        # The NVD API uses ISO 8601 format with 'T' separating date and time.
        formatted_start_date = start_date.isoformat(timespec='seconds') + 'Z'
        formatted_end_date = end_date.isoformat(timespec='seconds') + 'Z'

        # API parameters to get CVEs modified within the specified time window
        params = {
            'pubStartDate': formatted_start_date,
            'pubEndDate': formatted_end_date,
            'resultsPerPage': 100, # Fetch a reasonable number of results per page.
        }

        print(f"Fetching CVEs from {formatted_start_date} to {formatted_end_date}...")
        response = requests.get(NVD_API_URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes

        data = response.json()
        return data.get('vulnerabilities', [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching CVE data: {e}")
        return []

def format_cve_for_discord(cve_list):
    """
    Formats a list of CVEs into a message suitable for a Discord webhook.

    Args:
        cve_list (list): A list of CVE records.

    Returns:
        str: A formatted string for the Discord message.
    """
    if not cve_list:
        return "No new CVEs found in the last 24 hours. All clear! :white_check_mark:"

    summary_list = []
    # Sort CVEs by CVSS score (if available) from highest to lowest.
    sorted_cves = sorted(cve_list, key=lambda cve: (cve['cve']['metrics'].get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0), cve['cve']['id']), reverse=True)

    for cve_record in sorted_cves:
        cve = cve_record['cve']
        cve_id = cve['id']
        description = "No description available."
        # Find the English description
        for desc_obj in cve.get('descriptions', []):
            if desc_obj['lang'] == 'en':
                description = desc_obj['value']
                break
        
        # Get severity and base score from CVSS 3.1, if available
        severity = "N/A"
        base_score = "N/A"
        
        metrics = cve.get('metrics', {})
        cvss_v31 = metrics.get('cvssMetricV31', [])
        if cvss_v31:
            score_data = cvss_v31[0]['cvssData']
            base_score = score_data.get('baseScore')
            severity = cvss_v31[0].get('cvssStatus', 'N/A')

        # Create the summary string for this CVE
        summary = f"**{cve_id}**\n- **Severity**: {severity} (Score: {base_score})\n- **Summary**: {description[:200]}...\n- **Link**: https://nvd.nist.gov/vuln/detail/{cve_id}\n"
        summary_list.append(summary)

    # Combine all summaries into a single message
    message = "🔍 **Latest CVEs from NVD (Last 24 hours)** 🔍\n\n"
    message += "\n".join(summary_list)

    # Truncate the message if it exceeds Discord's 2000 character limit
    if len(message) > 1970:
        message = message[:1952] + "..." + "\n\n(Message truncated due to character limit.)"

    return message

def send_to_discord(message):
    """
    Sends a formatted message to a Discord channel via a webhook.

    Args:
        message (str): The message to send.
    """
    if not DISCORD_WEBHOOK_URL.startswith("http"):
        print("Webhook URL is not set. Please update the script with your Discord webhook URL.")
        return

    payload = {
        "content": message
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        print("Successfully sent CVE summary to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Discord: {e}")
        if response.status_code == 400:
            print(f"Bad Request: The payload may be malformed or too long. Response: {response.text}")
        elif response.status_code == 401:
            print("Unauthorized: The webhook URL is invalid.")
        elif response.status_code == 429:
            print("Rate limited: You are sending too many requests.")

# --- Main execution block ---
if __name__ == "__main__":
    cves = fetch_latest_cves()
    discord_message = format_cve_for_discord(cves)
    send_to_discord(discord_message)

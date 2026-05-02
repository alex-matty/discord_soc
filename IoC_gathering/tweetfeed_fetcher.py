#!/usr/bin/env python3

# Description : fetch latest IoCs from Tweetfeed and post them to a dedicated webhook
# Version     : 1.1
# Author      : Meganuke_ (Refactored by Gemini CLI)
# Date        : 2026-05-01
# Usage       : python3 tweetfeed_fetcher.py
# Notes       : Richly styled embeds, clustered by type, with state management and GMT-6 conversion

# Import required libraries
import requests
import json
import os
import time
from datetime import datetime, timedelta

# Static variables
URL = 'https://api.tweetfeed.live/v1/today'
# State file to track the last seen IoC and avoid duplicates
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_seen_ioc.txt")

# Load ENV variables from an .env file
def load_env(file_path=None):
  if file_path is None:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

  try:
    with open(file_path) as f:
      for line in f:
        if line.strip() and not line.startswith("#"):
          key, value = line.strip().split("=", 1)
          os.environ[key] = value
  except FileNotFoundError:
    print(f".env file not found at {file_path}")
    exit(1)

load_env()
WEBHOOK_URL = os.getenv('TWEETFEED_WEBHOOK')

# Converts UTC time from API to user's local time (GMT-6) for better context.
def utc_to_local(utc_date_str):
    try:
        # Input format: 2026-05-02 05:23:00
        utc_dt = datetime.strptime(utc_date_str, "%Y-%m-%d %H:%M:%S")
        local_dt = utc_dt - timedelta(hours=6)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S") + " (GMT-6)"
    except Exception:
        return utc_date_str

# Function to defang URL, IP or Domain names
def defang(value, type_):
  if type_ in ("ip", "domain"):
    return value.replace(".", "[.]")
  elif type_ == "url":
    value = value.replace("http", "hxxp")
    value = value.replace("://", "[://]")
    value = value.replace(".", "[.]")
    return value
  return value

# Enhanced style mapping with Emojis and Colors
TYPE_STYLE = {
    "url": {"color": 15158332, "emoji": "🌐"},    # Red / Globe
    "ip": {"color": 3447003, "emoji": "💻"},     # Blue / Computer
    "domain": {"color": 15844367, "emoji": "🏠"}, # Gold / House
    "sha256": {"color": 10181046, "emoji": "🔑"}, # Purple / Key
    "md5": {"color": 10181046, "emoji": "🔑"}     # Purple / Key
}

def send_payload(payload):
  try:
    response = requests.post(WEBHOOK_URL, json=payload, timeout=30) 
    response.raise_for_status()
    print(f"Sent batch of {len(payload['embeds'])} Embed(s) to Discord")
    time.sleep(1) 
  except requests.exceptions.RequestException as e:
    print(f"Failed to send batch: {e}")

def process_and_send(items):
  grouped = {}
  for item in items:
    itype = item['type']
    if itype not in grouped:
      grouped[itype] = []
    grouped[itype].append(item)

  current_batch = []
  current_batch_total_chars = 0
  
  for itype, itype_items in grouped.items():
    style = TYPE_STYLE.get(itype, {"color": 8359053, "emoji": "🔍"})
    
    # Start description with a bold summary
    itype_description = f"**{style['emoji']} Found {len(itype_items)} New {itype.upper()} Indicators**\n\n"
    
    for item in itype_items:
      tags_str = f" • **Tags**: `{', '.join(item['tags'])}`" if item['tags'] else ""
      line = f"• `{item['value']}`{tags_str}\n"
      
      if len(itype_description) + len(line) > 4000:
        embed = {
            "title": f"Threat Intelligence: {itype.upper()} (Continued)",
            "description": itype_description,
            "color": style['color'],
            "footer": {"text": f"Tweetfeed.live Feed • SOC Monitor"}
        }
        
        if current_batch_total_chars + len(embed["description"]) > 5500:
          send_payload({"embeds": current_batch})
          current_batch = []
          current_batch_total_chars = 0
        
        current_batch.append(embed)
        current_batch_total_chars += len(embed["description"])
        itype_description = f"**{style['emoji']} {itype.upper()} (Continued)**\n\n" + line
      else:
        itype_description += line

    if itype_description:
      local_date = utc_to_local(itype_items[0]['date'])
      embed = {
          "title": f"Threat Intelligence: {itype.upper()}",
          "description": itype_description,
          "color": style['color'],
          "footer": {"text": f"Tweetfeed.live Feed • {local_date}"}
      }
      
      if current_batch_total_chars + len(embed["description"]) > 5500:
        send_payload({"embeds": current_batch})
        current_batch = []
        current_batch_total_chars = 0
      
      current_batch.append(embed)
      current_batch_total_chars += len(embed["description"])

    if len(current_batch) >= 10:
      send_payload({"embeds": current_batch})
      current_batch = []
      current_batch_total_chars = 0

  if current_batch:
    send_payload({"embeds": current_batch})

# State management functions
def get_last_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return ""

def set_last_seen(date_str):
    with open(STATE_FILE, "w") as f:
        f.write(date_str)

def main():
  try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    data = response.json()
  except requests.exceptions.RequestException as e:
    print(f"Failed to fetch data: {e}")
    exit(1)
  
  last_seen = get_last_seen()
  new_items = [i for i in data if i["date"] > last_seen]
  new_items.sort(key=lambda x: x["date"])

  if not new_items:
    print("No new IoCs found since last run.")
    return

  processed_items = [
    {
      "date": item["date"],
      "type": item["type"],
      "value": defang(item["value"], item["type"]),
      "tags": item.get("tags", []),
    }
    for item in new_items
  ]
  
  process_and_send(processed_items)
  set_last_seen(new_items[-1]["date"])

if __name__ == "__main__":
  main()
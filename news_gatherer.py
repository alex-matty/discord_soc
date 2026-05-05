#!/usr/bin/env python3

# Description : Fetch RSS feeds and show the latest news in a discord channel 
# Version     : 1.0
# Author      : Meganuke_ (Refactored by Gemini CLI)
# Date        : 2026-05-01
# Usage       : python3 news_gatherer.py
# Notes       : Refactored for efficiency and visual appeal (Discord Embeds)

# Import required libraries
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import json
import os
from email.utils import parsedate_to_datetime

# Function to get .env variables
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
      print(f"Warning: .env file not found at {file_path}")

load_env()
WEBHOOK_URL = os.getenv('NEWS_GATHERER_WEBHOOK')

# Added 'color' and 'icon' to the feed dictionary
rss_feeds = {
  'the_hacker_news': {
      'url': 'https://feeds.feedburner.com/TheHackersNews',
      'color': 15158332, # Red
  },
  'bleeping_computer': {
      'url': 'https://www.bleepingcomputer.com/feed/',
      'color': 3447003, # Blue
  },
  'dark_reading': {
      'url': 'https://www.darkreading.com/rss.xml',
      'color': 15844367, # Gold/Yellow
  }
}

def xml_to_json_payload_sender():
  if not WEBHOOK_URL:
    print("Error: NEWS_GATHERER_WEBHOOK not set in environment.")
    return

  now = datetime.now(timezone.utc)
  time_threshold = now - timedelta(hours=24)

  for feed_name, config in rss_feeds.items():
    url = config['url']
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
      print(f'Fetching News from {feed_name}')
      response = requests.get(url, headers=headers, timeout=30)
      response.raise_for_status()
      
      root = ET.fromstring(response.content)
      
      news_items = []
      for item in root.findall('.//item'):
        title = item.find('title').text if item.find('title') is not None else "No Title"
        link = item.find('link').text if item.find('link') is not None else ""
        pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else None
        
        if pub_date_str:
          try:
            pub_date = parsedate_to_datetime(pub_date_str)
            if pub_date.tzinfo is None:
              pub_date = pub_date.replace(tzinfo=timezone.utc)
            
            if pub_date > time_threshold:
              news_items.append(f"• [{title.strip()}]({link.strip()})")
          except Exception as e:
            continue

      if not news_items:
        print(f'No new entries found for {feed_name}, skipping')
        continue

      print(f'Found {len(news_items)} entries for {feed_name}')

      # Instead of "content", we use the "embeds" array. This creates a card with 
      # a side-color, a header, and a cleaner link list.
      
      embed = {
          "title": f"Latest News: {feed_name.replace('_', ' ').title()}",
          "description": "\n".join(news_items),
          "color": config['color'],
          "timestamp": now.isoformat(), # Adds the time at the bottom of the card
          "footer": {
              "text": f"SOC News Gatherer • {len(news_items)} articles"
          }
      }

      # Discord takes an array of embeds (up to 10 per message)
      payload = {
          "embeds": [embed]
      }
      
      # Truncate description if it exceeds Discord's 4096 limit for embeds
      if len(embed["description"]) > 4000:
          embed["description"] = embed["description"][:3990] + "..."

      post_request = requests.post(WEBHOOK_URL, json=payload, timeout=30)
      post_request.raise_for_status()
      print(f'Successfully Sent {feed_name} Embed to Discord')

    except Exception as e:
      print(f'Error processing {feed_name}: {e}')

if __name__ == "__main__":
  xml_to_json_payload_sender()

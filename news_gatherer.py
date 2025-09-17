#!/usr/bin/env python3

# Description : Fetch RSS feeds and show the latest news in a discord channel 
# Version     : 0.6
# Author      : Meganuke_
# Date        : 2025-09-16
# Usage       : python3 news_gatherer.py
# Notes       : TODO - Improve readability

# Import required libraries
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
import glob

# Function to validated json payload
def is_valid_json(json_string):
  try:
    json.dumps(json_string)
    return True
  except ValueError:
    return False

# Set the RSS feed names you will use in a dictionary
rss_feed_name = [
  'the_hacker_news',
  'bleeping_computer',
  'dark_reading'
]

# Set the RSS feed URLs to use in a dictionary
rss_feed_url =[ 
  'https://feeds.feedburner.com/TheHackersNews',
  'https://www.bleepingcomputer.com/feed/',
  'https://www.darkreading.com/rss.xml'
]

# Set the ENV variable to be used in the function
webhook = os.environ['NEWS_GATHERER_WEBHOOK']

# Set the date as a variable to get the correct formatting to get rid of the old entries
today_date = datetime.now()
formatted_date = today_date.strftime('%d %b %Y')
next_day_date = today_date + timedelta(days=1)
formatted_next_date = next_day_date.strftime('%d %b %Y')

def xml_to_json_payload_sender(rss_feed, rss_url):
  for feed, url in zip(rss_feed, rss_url):
    variable_prefix = feed 
    rss_feed_xml_url = url

    # Set the headers for a more friendly user agent
    headers = {
      'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # GET request to obtain the XML and store it in a file to be able to handle it
    url_response = requests.get(rss_feed_xml_url, headers=headers)
    
    with open(f'{variable_prefix}.xml', 'w', encoding='utf-8') as file:
      file.write(url_response.text)

    # Parse the contents to get only the required data
    feed_parsed_xml = ET.parse(f"{variable_prefix}.xml",)
    root = feed_parsed_xml.getroot()

    # Create a new_item_counter to understand what items have today's date
    new_item_counter = 0
    for news_date in root.iter():
      if news_date.tag in ['pubDate']:
        if formatted_date in news_date.text or formatted_next_date in news_date.text:
          new_item_counter+=1

    # Iterate over the XML file and write it in a dirty file to use as first iteration
    with open(f'{variable_prefix}.xml_dirty', 'w') as file:
      for element in root.iter():
        if element.tag in ['title', 'link', 'pubDate']:
          file.write(element.text + "\n")

    # Iterate over the dirty file to get rid of old entries
    counter = 0
    with open(f'{variable_prefix}.xml_cleaned', 'w') as file:
      with open(f'{variable_prefix}.xml_dirty', 'r') as file2:
        for line in file2:
          file.write(line)
          if formatted_date in line or formatted_next_date in line:
            counter+=1
            if counter == new_item_counter:
                break

    # Remove date lines from the cleaned file
    with open(f'{variable_prefix}.xml_cleaned', 'r') as file:
      with open(f'{variable_prefix}.xml_no_date', 'w') as file2:
        for line in file:
          if formatted_date not in line and formatted_next_date not in line:
            file2.write(line)

    # Convert text to json and add the correct formatting by creating a dictionary
    with open(f'{variable_prefix}.xml_no_date', 'r') as file:
      with open(f'{variable_prefix}.json_dirty', 'w') as file2:
        counter = 1
        for line in file:
          if counter == 1:
            file2.write(f'# **[{line.strip()}]')
          elif counter == 2:
            file2.write(f'({line.strip()})**\n')
          elif counter % 2 != 0:
            file2.write(f'- [{line.strip()}]')
          else:
            file2.write(f'({line.strip()})\n')
          counter+=1

    # Store the content of the file in a variable and create a key value pair in the correct json syntax
    with open(f'{variable_prefix}.json_dirty', 'r') as file:
      json_payload = file.read()

    json_payload_sent = {
      "content": json_payload,
      "flags": 4
    }

    # Send the json file to the discord webhook
    webhook = os.environ['NEWS_GATHERER_WEBHOOK']
    request_headers = {
      "Content-Type": "application/json"
    }

    # validate the json to verify it's valid output and send only if valid
    if new_item_counter != 0:
      if is_valid_json(json_payload_sent) == True:
        # Send the POST request to the webhook
        post_request = requests.post(webhook, headers=request_headers, json=json_payload_sent)
      else:
        break

    # Delete files after use
    for file in glob.glob(f'{variable_prefix}*'):
      try:
        os.remove(file)
      except Exception as e:
        break

# Execute the function calling the feeds
xml_to_json_payload_sender(rss_feed_name, rss_feed_url)

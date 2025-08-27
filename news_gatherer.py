#!/usr/bin/env python3

# Create an iterative function to send the RSS feeds to Discord via webhook

# Import required libraries
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
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
  'the_hacker_news'
#  'bleeping_computer',
]

# Set the RSS feed URLs to use in a dictionary
rss_feed_url =[ 
  'https://feeds.feedburner.com/TheHackersNews'
#  'https://www.bleepingcomputer.com/feed/',
]

# Set the ENV variable to be used in the function
webhook = os.environ['NEWS_GATHERER_WEBHOOK']

# Set the date as a variable to get the correct formatting to get rid of the old entries
today_date = datetime.now()
formatted_date = today_date.strftime('%d %b %Y')

def xml_to_json_payload_sender(rss_feed, rss_url):
  for feed, url in zip(rss_feed, rss_url):
    variable_suffix = feed 
    rss_feed_xml_url = url

    # GET request to obtain the XML and store it in a file to be able to handle it
    url_response = requests.get(rss_feed_xml_url)
    
    with open(f'{variable_suffix}.xml', 'w', encoding='utf-8') as file:
      file.write(url_response.text)

    # Parse the contents to get only the required data
    feed_parsed_xml = ET.parse(f"{variable_suffix}.xml",)
    root = feed_parsed_xml.getroot()

    # Create a counter to understand what items have today's date
    counter = 0
    for news_date in root.iter():
      if news_date.tag in ['pubDate']:
        if formatted_date in news_date.text:
          counter+=1

    # Iterate over the XML file and write it in a dirty file to use as first iteration
    with open(f'{variable_suffix}.xml_dirty', 'w') as file:
      for element in root.iter():
        if element.tag in ['title', 'link', 'pubDate']:
          file.write(element.text + "\n")

    # Iterate over the dirty file to get rid of old entries
    counter2 = 0
    with open(f'{variable_suffix}.xml_cleaned', 'w') as file:
      with open(f'{variable_suffix}.xml_dirty', 'r') as file2:
        for line in file2:
          file.write(line)
          if formatted_date in line:
            counter2+=1
            if counter2 == counter:
                break

    # Remove date lines from the cleaned file
    with open(f'{variable_suffix}.xml_cleaned', 'r') as file:
      with open(f'{variable_suffix}.xml_no_date', 'w') as file2:
        for line in file:
          if formatted_date not in line:
            file2.write(line)

    # Convert text to json and add the correct formatting by creating a dictionary
    with open(f'{variable_suffix}.xml_no_date', 'r') as file:
      with open(f'{variable_suffix}.json_dirty', 'w') as file2:
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
    with open(f'{variable_suffix}.json_dirty', 'r') as file:
      json_payload = file.read()

    json_payload_sent = {
      "content": json_payload,
      "flags": 4
    }

    # Send the json file to the discord webhook
    # webhook = os.environ['NEWS_GATHERER_WEBHOOK'] 
    request_headers = {
      "Content-Type": "application/json"
    }

    # validate the json to verify it's valid output
    #print(is_valid_json(json_payload_sent))

    # Send the POST request to the webhook
    post_request = requests.post(webhook, headers=request_headers, json=json_payload_sent)
    
    # Delete files after use
    for file in glob.glob(f'{variable_suffix}*'):
      try:
        os.remove(file)
      except Exception as e:
        break

# Execute the function calling the lists
xml_to_json_payload_sender(rss_feed_name, rss_feed_url)

# Unset ENV variables to keep it clean
# os.environ.pop('NEWS_GATHERER_WEBHOOK', None)

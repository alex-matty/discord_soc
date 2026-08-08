#!/usr/bin/env python3

# Description : Query abuseIPDB in order to gather information from an IP or report malicious IPs to the service
# Version     : 0.1
# Author      : Meganuke_
# Date        : 2025-09-18
# Usage       : ./abuseipdb_query.py
# Notes       : TODO - Create the first part to query IP information

# Import required libraries
import requests
import json
import os

abuseipdb_key = os.environ['ABUSEIPDB_API_KEY']

def check_endpoint():
  ip_address = input('IP to check: ')
  abuseipdb_url = 'https://api.abuseipdb.com/api/v2/check'

  query_string = {
    'ipAddress': ip_address,
    'maxAgeInDays': '90'
  }

  headers = {
    'Accept': 'application/json',
    'Key': abuseipdb_key
  }

  response = requests.get(url=abuseipdb_url, headers=headers, params=query_string)

  print(f'{ip_address} information:')

  decoded_response = json.loads(response.text)
  print(json.dumps(decoded_response, sort_keys=True, indent=2))

if __name__ == '__main__':
  check_endpoint()

#!/usr/bin/env bash

# Create a script that reports a banned IP from Fail2Ban

# Set the dir_name to use as a base for the absolute path of the .env file
dir_name=$(dirname "$0")

# Get the API key from .env file and check if it has been properly set
ABUSE_IPDB_API_KEY=$(grep -E '^ABUSE_IPDB_API_KEY' "$dir_name/../../.env" | cut -d '=' -f 2 | tr -d '"' | tr -d "'")

if [ -z "$ABUSE_IPDB_API_KEY" ]; then
  echo 'Error: AbuseIPDB API Key not found in .env file.'
  exit 1
fi

# Get the IP from the ip_ban_monitor script
ip_address=$1

# Set the correct timestamp to use for the reporting parameters
timestamp=$(date +"%Y-%m-%dT%H:%M:%S%:z")

# Report IP with the desired parameters
# POST the submission.
curl_status_code=$(curl https://api.abuseipdb.com/api/v2/report -o /dev/null -s -w "%{http_code}\n" \
  --data-urlencode "ip=$ip_address" \
  -d categories=18,22 \
  --data-urlencode "comment=SSH brute force login attempts." \
  --data-urlencode "timestamp=$timestamp" \
  -H "Key: $ABUSE_IPDB_API_KEY" \
  -H "Accept: application/json")

# Handle different response status codes
if [ "$curl_status_code" -eq 200 ]; then
  echo "IP has been reported to AbuseIPDB."
elif [ "$curl_status_code" -eq 429 ]; then
  echo "You can only report the same IP address once in 15 minutes."
elif [ "$curl_status_code" -ge 400 ] && [ "$curl_status_code" -le 499 ]; then
  echo "There is an unknown error at the client side."
elif [ "$curl_status_code" -ge 500 ] && [ "$curl_status_code" -le 599 ]; then
  echo "There is an unknown error at the server side."
else
  echo "Unknown status code received."
fi

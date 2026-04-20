#!/usr/bin/env python3

# Description : fetch latest IoCs from Tweetfeed and post them to a dedicated webhook
# Version     : 0.1
# Author      : Meganuke_
# Date        : 2026-04-19
# Usage       : python3 tweetfeed_fetcher.py
# Notes       : -

# Import required libraries
import requests
import json
import os

# Static variables used for the main script
URL = 'https://api.tweetfeed.live/v1/today'
CHAR_LIMIT = 2000
DISCORD_PAYLOAD_OVERHEAD = 30
EFFECTIVE_LIMIT = CHAR_LIMIT - DISCORD_PAYLOAD_OVERHEAD

# Load ENV variables from an .env file into os.environ
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

# Get Webhook URL address from the .ENV file
load_env()
WEBHOOK_URL = os.getenv('TWEETFEED_WEBHOOK')


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

# Define the truncate function to not pass the message length limit
def truncate_content(content):
  if len(content) > EFFECTIVE_LIMIT:
    truncated = content[:EFFECTIVE_LIMIT -7]
    return truncated + "\n...\n```"
  return content

# Function to create the main discord payload block and send it to the webhook
def flush_chunk(chunk):
  content = f"```json\n{json.dumps(chunk, indent=2)}\n```"
  content = truncate_content(content)

  discord_payload = {
    "content": content,
    "flags": 4
  }

  try:
    response = requests.post(WEBHOOK_URL, json=discord_payload) 
    response.raise_for_status()
    print(f"Sent {len(chunk)} item(s) to Discord ({len(content)} chars)")
  except requests.exceptions.RequestException as e:
    print(f"Failed to send chunk to discord: {e}")

# Build and send Chunked discord payloads
# If a payload is greater than the length, create a new payload
def send_to_discord(items):
  chunk = []
  
  for item in items:
    chunk.append(item)

    content = f"```json\n{json.dumps(chunk, indent=2)}\n```"
    total_len = len(json.dumps({"content": content, "flags": 4}))

    if total_len > CHAR_LIMIT:
      chunk.pop()
      flush_chunk(chunk)
      chunk = [item]

  if chunk:
    flush_chunk(chunk)

def main():
  # Fetch and parse today's IoC feed. Exit early if the API is unreachable or returns an error 
  try:
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()
  except requests.exceptions.RequestException as e:
    print(f"Failed to fetch data: {e}")
    exit(1)
  
  # Select only relevant fields and defang values to prevent accidental resolution
  json_payload = [
    {
      "date": item["date"],
      "type": item["type"],
      "value": defang(item["value"], item["type"]),
      "tags": item["tags"],
    }
    for item in data
  ]
  
  send_to_discord(json_payload)

if __name__ == "__main__":
  main() 
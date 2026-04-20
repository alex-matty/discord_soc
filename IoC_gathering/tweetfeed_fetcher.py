#!/usr/bin/env python3

# Import required libraries
import requests
import json
import re
import os

# Get .ENV variables from an .ENV file
def load_env(file_path=None):
  if file_path is None:
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(file_path) as f:
      for line in f:
        if line.strip() and not line.startswith("#"):
          key, value = line.strip().split("=", 1)
          os.environ[key] = value

load_env()

# Function to defang URLs or Domain names
def defang(value, type_):
  if type_ in ("ip", "domain"):
    return value.replace(".", "[.]")
  elif type_ == "url":
    value = value.replace("http", "hxxp")
    value = value.replace("://", "[://]")
    value = value.replace(".", "[.]")
    return value
  return value

# Build and send Chunked discord payloads
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


def truncate_content(content):
  if len(content) > EFFECTIVE_LIMIT:
    truncated = content[:EFFECTIVE_LIMIT -7]
    return truncated + "\n...\n```"
  return content

def flush_chunk(chunk):
  content = f"```json\n{json.dumps(chunk, indent=2)}\n```"
  content = truncate_content(content)

  discord_payload = {
    "content": content,
    "flags": 4
  }

  response = requests.post(WEBHOOK_URL, json=discord_payload)

  print(f"status: {response.status_code}")
  print(f"Response: {response.text}")
  print(f"Content Length: {len(content)}")

  response.raise_for_status()
  print(f"Sent {len(chunk)} item(s) to Discord ({len(content)} chars)")

# Tweetfeed API URL endpoint (@TODO Add variables to use filters)
url = 'https://api.tweetfeed.live/v1/today'
WEBHOOK_URL = os.getenv('TWEETFEED_WEBHOOK')
CHAR_LIMIT = 2000
CODE_BLOCK = 15 
DISCORD_PAYLOAD_OVERHEAD = 30
EFFECTIVE_LIMIT = CHAR_LIMIT - DISCORD_PAYLOAD_OVERHEAD

# Make the request to the API feed URL
response = requests.get(url)

# Parse JSON object
data = response.json()

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

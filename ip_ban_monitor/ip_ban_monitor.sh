#!/usr/bin/env bash

# This one will be used to detect a log entry that is shown as banned 

LOG_FILE="/var/log/fail2ban.log"
# Embed will be red as it states a blocked IP
EMBED_COLOR='15158332'

# Get the webhook URL from an .env file without sourcing it 
WEBHOOK=$(grep -E '^FAIL2BAN_WEBHOOK=' .env | cut -d '=' -f 2 | tr -d '"' | tr -d "'")

# Check if webhook is present otherwise exit 
if [ -z "$WEBHOOK" ]; then
  echo 'Error: Fail2Ban webhook not found in .env file.'
  exit 1
fi

# Read the log entries in real time and find only banned IPs
tail -f "$LOG_FILE" | while IFS= read -r line; do

  if [[ "$line" == *"NOTICE"*"[sshd] Ban"* ]]; then
    
    # Get the IP from the message
    ip_address=$(echo $line | grep --line-buffered -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sed 's/\./[.]/g')
    extracted_timestamp=$(echo $line | awk '{print $1 $2}')

    json_payload=$(jq -n -c \
      --arg title "Fail2Ban IP Block Notification" \
      --arg color "$EMBED_COLOR" \
      --arg ip "$ip_address" \
      --arg log_level "Blocked" \
      --arg msg "IP Blocked for 24 hours" \
      --arg timestamp "$extracted_timestamp" \
      '{
        embeds: [
          {
            title: $title,
            color: ($color | tonumber),
            fields: [
              { name: "Banned IP Address", value: $ip, inline: true },
              { name: "Extracted Timestamp", value: $timestamp, inline: true },
              { name: "Report Level", value: $log_level, inline: false },
              { name: "Details", value: $msg, inline: false },
              { name: "Report Category", value: "Brute Force, SSH", inline: false }
            ],
          }
        ]
      }')

    # Send Payload to discord webhook
    curl -H "Content-Type: application/json" -X POST -d "$json_payload" "$WEBHOOK"

  fi

done

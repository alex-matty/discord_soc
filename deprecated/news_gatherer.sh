#!/bin/bash

##############################################################
# Created by @meganuke_ -------------------------------------#
# This script can be used, modify, replicate for any purpose #
# without any restrictions. ---------------------------------#
# Version: 0.1 ----------------------------------------------#
##############################################################

# UPDATES:
# Add 1 or 2 more sources of news
# URL decode messages to get them with the correct syntatx
# Add link for each blog entrance (bleeping computer done, hackerone seems to be done)
# Fix bug of the add being fecthed by hackernews.

#---------------------------------- Hacker news -----------------------------------#

# Fectch the html code from the site and save it in a file called hackernews.html in order to parse it.
curl -s -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0" https://thehackernews.com/ > hackernews.html

# Today's date in post's date format to compare with post entries
today_date=$(date "+%b %d, %Y")
# Get the dates of the posts to compare with previous dates and only report new post for the current day.
cat hackernews.html | grep -oE "<span class='h-datetime'>.*</span>" | sed "s/<span class='h-datetime'><i class='icon-font icon-calendar'>//g" | sed 's/&#59394;<\/i>//g' | sed 's/<\/span>//g' > hackernews.dates
# Iterate over the hackernews.dates file in order to count only the dates that are equal to today's date.
entries=0
while read lines; do
	if [[ $today_date == $lines ]]; then
		((entries++))
	fi
done < hackernews.dates > hackernews.today

# Parse HTML to retrieve only the blog titles and create a file called hackernews.titles to use for future JSON formatting.
cat hackernews.html | grep -o "<h2 class='home-title'>.*<\/h2>" | sed 's/<img.*//g' | sed "s/<h2\ class='home-title'>//g" | sed "s/<.*//g" | sed '/^$/d' | sed 's/"/\\"/g'  | head -$entries > hackernews.titles
# Parse HTML to retrieve only the blog adresses and create a file called hackernews.adresses to use for future json formatting.
cat hackernews.html | grep -oE "<a class='story-link'.*>" | grep -E 'href="https://thehackernews.com/.*.html' | sed "s/<a class='story-link'//g" | sed 's/href="//g' | sed 's/">//g' | head -$entries> hackernews.adresses

# Add the titles the symbol "-" and the square brackets to each line of the file to create link text in markdown and cat the output to a file called hackernews.texts which then be used to concatt lines to continue with the JSON formating.
while read lines; do
	echo - "[$lines]"
done < hackernews.titles | head -$entries >> hackernews.texts
# Add the links symbol the "()" to each line of the file to create link to follow in markdown and cat the output to a file called hackernews.texts which then be used to concatt lines to continue with the JSON formating.
while read lines2; do
	echo "($lines2)"
done < hackernews.adresses >> hackernews.links

# Add the first part of the JSON file to start formatting the JSON output to a json.dirty file
echo "{ \"content\": \"# **https://www.thehackernews.com**" > hackernews.json.dirty
# Read the two files and concatentate in each line the text and the link to have the proper markdown syntax
while IFS= read -r line1 && IFS= read -r line2 <&3; do
  echo -n "$line1"
  echo "$line2"
done < hackernews.texts 3< hackernews.links >> hackernews.json.dirty
# Transform the content of the json.dirty file into correct JSON syntax adding the "\n" symbol to separate the lines in the message for correct syntax
cat hackernews.json.dirty | sed -z 's/\n/\\n/g' | sed 's/\\n$/\", "flags": 4 }/g' >> hackernews.json 

# Send the content of the corrected and complete json file to discord via webhook address
curl -X POST -H "Content-Type: application/json" -d @hackernews.json $NEWS_GATHERER_WEBHOOK 

# Wait 5 seconds to start with the second source of news.
sleep 5

#---------------------------------- Bleeping Computer -----------------------------------#

# Fectch the html code from the site and save it in a file called bleepingcomputer.html in order to parse it.
curl -s -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0" https://www.bleepingcomputer.com/ > bleepingcomputer.html

# Today's date in post's date format to compare with post entries
today_date=$(date "+%B %d, %Y")
# Get the dates of the posts to compare with previous dates and only report new post for the current day.
cat bleepingcomputer.html | grep -oE '<li class="bc_news_date">.*<\/li>' | sed 's/<li class=//g' | sed 's/"bc_news_date">//g' | sed 's/<\/li>//g' > bleepingcomputer.dates
# Iterate over the hackernews.dates file in order to count only the dates that are equal to today's date.
entries=0
while read lines; do
	if [[ $today_date == $lines ]]; then
		((entries++))
	fi
done < bleepingcomputer.dates > bleepingcomputer.today

# Parse HTML to retrieve only the blog titles and create a file called hackernews.titles to use for future JSON formatting.
cat bleepingcomputer.html | grep '<h4>.*<\/h4>' | awk '!/<h4><a href="https:\/\/www\.bleepingcomputer\.com\/news\/security\//{$0=""}1' | sed '/^$/d' | sed 's/<h4.*">//g' | sed 's/<\/a.*//g' | sed 's/"/\\"/g' | head -$entries >> bleepingcomputer.titles
# Parse HTML to retrieve only the blog adresses and create a file called hackernews.adresses to use for future json formatting.
cat bleepingcomputer.html | grep '<h4>.*<\/h4>' | awk '!/<h4><a href="https:\/\/www\.bleepingcomputer\.com\/news\/security\//{$0=""}1' | sed 's/<h4>//g' | sed 's/<\/h4>//g' | grep -oE 'https:\/\/www\.bleepingcomputer\.com\/news\/security\/.*\/"' | sed s'/"//g' | head -$entries > bleepingcomputer.adresses

# Add the titles the symbol "-" and the square brackets to each line of the file to create link text in markdown and cat the output to a file called hackernews.texts which then be used to concatt lines to continue with the JSON formating.
while read lines; do
	echo - "[$lines]"
done < bleepingcomputer.titles | head -$entries >> bleepingcomputer.texts
# Add the links symbol the "()" to each line of the file to create link to follow in markdown and cat the output to a file called hackernews.texts which then be used to concatt lines to continue with the JSON formating.
while read lines2; do
	echo "($lines2)"
done < bleepingcomputer.adresses >> bleepingcomputer.links

# Add the first part of the JSON file to start formatting the JSON output to a json.dirty file
echo "{ \"content\": \"# **https://www.bleepingcomputer.com/**" > bleepingcomputer.json.dirty
# Read the two files and concatentate in each line the text and the link to have the proper markdown syntax
while IFS= read -r line1 && IFS= read -r line2 <&3; do
  echo -n "$line1"
  echo "$line2"
done < bleepingcomputer.texts 3< bleepingcomputer.links >> bleepingcomputer.json.dirty
# Transform the content of the json.dirty file into correct JSON syntax adding the "\n" symbol to separate the lines in the message for correct syntax
cat bleepingcomputer.json.dirty | sed -z 's/\n/\\n/g' | sed 's/\\n$/\", "flags": 4 }/g' >> bleepingcomputer.json

# Send the content of the corrected and complete json file to discord via webhook address
curl -X POST -H "Content-Type: application/json" -d @bleepingcomputer.json $NEWS_GATHERER_WEBHOOK

# Remove all previously created files used for parsing and formatting the JSON file and the JSON files used to send the information
rm hackernews.* bleepingcomputer.*	

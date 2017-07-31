import sys
sys.path.append("c:/users/matt/anaconda3/lib/site-packages")

import requests
from bs4 import BeautifulSoup
import urllib
import random

alphanums = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

####
####
### TODO: Add dictionary to make sure that the primary key is unique and consider adding primary key + match link to db



# https://www.hltv.org/results?offset=100&map=de_inferno
# only working with inferno for now.
# just change the url and it should get all results.

#exclude trailing / as it's included in the links obtained from site
host = 'https://www.hltv.org'
dl_location = 'D:\CSGOProGames\_rawfiles'

# also going to just increment the offset in python rather than follow the url on the page
offset = 0
# using underscore for readability
all_links = []
match_links = []
dl_links = []
dem_files = []
hltvlink = []

# Get all the links on the results page
# filtered results page
while offset <= 99: # get most recent 600 games ~3 mos worth
    req = requests.get(host + "/results?map=de_inferno&offset={!s}".format(offset))
    print(req) # gives html status code
    soup = BeautifulSoup(req.content, 'html.parser')
    all_links = soup.find_all('a', class_='a-reset') # class from html that holds the urls (result-con didn't work...?)
    offset += 100 # hltv.org shows 100 results per page (didn't bother to check if there is a way to change this value).

# filtering incorrect links by getting rid of forum, vod, blog, etc. links
for link in all_links:
    link = link.get('href')
    if 'matches' in link:
        match_links.append(link)

# following correct match links to find download links
for i,link in enumerate(match_links):
    req = requests.get("https://www.hltv.org{!s}".format(link))
    print(req)
    soup = BeautifulSoup(req.content, 'html.parser')
    dl_links.append(soup.find_all('a', class_='flexbox left-right-padding')) # GOTV demo class
    if i > 5:
        break

for link in zip(dl_links, match_links):
    dem_files.append([link[0][0].get('href'),link[1]]) # Pairing download link with match info link for eventual use by user

# From stack overflow: ...some sites (including Wikipedia) block on common non-browser user agents strings, like the
# "Python-urllib/x.y" sent by Python's libraries. Even a plain "Mozilla" or "Opera" is usually enough to bypass that.
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers = {'User-Agent': user_agent,}

for demdl in dem_files:
    url = host + demdl[0]
    req = urllib.request.Request(url, None, headers)
    dl = urllib.request.urlopen(req)
    # DL link is a redirect
    # Get the file name from the url
    primarykey = ''.join(random.choices(alphanums, k=8))  # high entropy string to create external id - help keep output files together
    hltvlink.append(primarykey, demdl[1])
    filename = primarykey + '_' + dl.geturl().split('/')[-1]
    with open(dl_location + filename, 'wb') as file:
        file.write(dl.read())

# with open(dl_location + 'hltvlinks.csv', 'wb') as tvlinks:
#

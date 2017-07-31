import sys
sys.path.append("c:/users/matt/anaconda3/lib/site-packages")

import requests
from bs4 import BeautifulSoup
import urllib

# https://www.hltv.org/results?offset=100&map=de_inferno
# only working with inferno for now.
# just change the url and it should get all results.

# also going to just increment the offset in python rather than follow the url on the page
offset = 0
links = []

# Get all the links on the results page
while offset <= 99: # get most recent 6000 games ~3 mos worth
    req = requests.get("https://www.hltv.org/results?map=de_inferno&offset={!s}".format(offset))
    soup = BeautifulSoup(req.content, 'html.parser')

    links = soup.find_all('a', string=r'*matches*') # class from html that holds the results url - this div is closed between events so hopefully bs will still find them all.
    offset += 100 #hltv.org shows 100 results per page (didn't bother to check if there is a way to change this value).

print(links)


dl = urllib.request.urlretrieve(links[20]) # I think this link will contain the file name.
print(dl.info)
dem = open('test.dem')
dem.close()
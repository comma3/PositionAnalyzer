import requests
from bs4 import BeautifulSoup


# https://www.hltv.org/results?offset=100&map=de_inferno
# only working with inferno for now.
# just change the url and it should get all results.

# also going to just increment the offset in python rather than follow the url on the page
offset = 0
links = []

# Get all the links on the results page
while offset <= 600: # get most recent 6000 games ~3 mos worth
    req = requests.get("https://www.hltv.org/results?map=de_inferno&offset={!s}".format(offset))
    soup = BeautifulSoup(req.text, 'html.parser')
    links.append(soup.find_all('a', class_="result-con")) # class from html that holds the results url - this div is closed between events so hopefully bs will still find them all.
    offset += 100 #hltv.org shows 100 results per page (didn't bother to check if there is a way to change this value).

for link in links:
    soup = BeautifulSoup(html_doc, 'html.parser')
    soup.find_all("a", string="GOTV Demo")

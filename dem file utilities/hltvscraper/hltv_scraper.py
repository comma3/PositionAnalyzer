import requests
from bs4 import BeautifulSoup
import urllib
import random
import time
import datetime
import csv

# used for external key generation
alphanums = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def hltv_demscraper(site='https://www.hltv.org', dl_location='D:/CSGOProGames/!rarfiles/'):
    # exclude trailing / in site as it's included in the links obtained from site

    # Going to just increment the offset in the GET request in python rather than follow the url on the page
    offset = 0
    # using underscore for readability
    all_links = []
    match_links = []
    dl_links = []
    hltv_links = []
    errors = []

    # Get all the links on the results page
    # filtered results page
    while offset <= 99: # get most recent 600 games ~3 mos worth
        req = requests.get(site + "/results?offset={!s}".format(offset))
        print('HLTV result page status:')
        print(req)  # gives html status code
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
        soup = BeautifulSoup(req.content, 'html.parser')
        # Get the download link from the match page and pair it with the match link for use by users to find exact games
        dl_links.append([soup.find_all('a', class_='flexbox left-right-padding')[0].get('href'), link]) # GOTV demo class
        if i > 2:
            break

    # From stack overflow: ...some sites (including Wikipedia) block on common non-browser user agents strings, like the
    # "Python-urllib/x.y" sent by Python's libraries. Even a plain "Mozilla" or "Opera" is usually enough to bypass that.
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent': user_agent,}

    for demdl in dl_links:
        try: # Keep chugging if there's an error
            # Download files from 1 am until noon while I'm away.
            if datetime.datetime.now().hour > 12:
                # Sleep until
                print('Sleeping... ' + datetime.datetime.now().strftime("%c"))
                time.sleep(1) # sleep time in seconds (hours * mins * seconds)
                print('Back to work! ' + datetime.datetime.now().strftime("%c"))

            # Generate high entropy string to create external id - help keep output files together
            external_code = ''.join(random.choices(alphanums, k=8))
            print('Downloading ' + demdl[1])
            url = site + demdl[0]
            req = urllib.request.Request(url, None, headers)
            dl = urllib.request.urlopen(req)
            # DL link is a redirect
            # Get the file name from the url
            hltv_links.append([demdl[1], external_code])
            filename = external_code + '_' + dl.geturl().split('/')[-1]
            with open(dl_location + filename, 'wb') as file:
                file.write(dl.read())
        except:
            errors.append([filename, url, req])

    # TODO: Refactor this with my library
    with open(dl_location + 'ExternalCodes.csv', 'w') as csvfile:
        matchwriter = csv.writer(csvfile, delimiter=',', newline='\n')
        for row in hltv_links:
            matchwriter.writerow(row)

    with open(dl_location + 'Errors.csv', 'w') as csvfile:
        errorwriter = csv.writer(csvfile, delimiter=',', newline='\n')
        for row in errors:
            errorwriter.writerow(row)

if __name__ == '__main__':
    hltv_demscraper()
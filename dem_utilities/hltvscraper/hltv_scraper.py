import requests
import urllib
import random
import time
import datetime
import string
import os
import glob

from bs4 import BeautifulSoup

from hltv_unrar import *

import MFLibrary as mf

from subprocess import call


# used for external key generation
alphanums = string.ascii_letters + string.digits

def get_match_links(searchdepth=100, site='https://www.hltv.org'):
    """Gets all the links on the results page"""

    # Going to just increment the offset in the GET request in python rather than follow the url on the page
    offset = 0
    # Keep a running list of match links so we don't get duplicates
    # TODO: Change to sql query after db is populated
    match_db = mf.csv.read_list('match_db.csv')

    match_links = []

    while offset <= searchdepth:  # get most recent N matches
        try:
            req = requests.get(site + "/results?offset={!s}".format(offset))
            print('HLTV result page status:')
            print(req)  # gives html status code
            soup = BeautifulSoup(req.content, 'html.parser')
            all_links = soup.find_all('a', class_='a-reset') # class from html that holds the urls (result-con didn't work...?)
            offset += 100 # hltv.org shows 100 results per page (didn't bother to check if there is a way to change this value).
        except:
            # Got rejected once or twice
            # Wait 1 minute and try again
            time.sleep(60)
            pass

    print("Got links!")
    # filtering incorrect links by getting rid of forum, vod, blog, etc. links
    for link in all_links:
        link = link.get('href')
        # Collect until you found an old one
        if link in match_db:
            # We have reached links that we already collected.
            return match_links
        if 'matches' in link:
            match_links.append(link)

    # Should only hit this on first run
    return match_links


def find_demo_links(match_links, site='https://www.hltv.org', outputpath='D:/CSGOProGames/processed/'):
    """Find the actual demo file download link and output a list of match links (for end users),
    demo dl links, and external ids"""

    dl_links = []
    for link in match_links:
        req = requests.get(site+link)
        soup = BeautifulSoup(req.content, 'html.parser')
        # Generate high entropy string to create external id - help keep output files together
        external_code = ''.join(random.choices(alphanums, k=8))
        # Get the download link from the match page and pair it with the match link for use by users to find exact games
        try:
            dl_links.append([external_code, link, soup.find_all('a', class_='flexbox left-right-padding')[0].get('href')])  # GOTV demo class
        except IndexError:
            # Sometimes matches don't have uploaded DEM files
            print(["Issue finding dem file (probably does not exist)", link, req])

    print(dl_links)
    # Include date + hour in case it gets run twice in a day
    mf.csv.write_list(outputpath + datetime.datetime.now().strftime("!%Y-%m-%d-%H_links_extid.csv"), dl_links)
    return dl_links


def download_dems(dl_links, site='https://www.hltv.org', dl_location='D:/CSGOProGames/rar/'):
    """Follows download links and downloads files"""
    # exclude trailing / in site as it's included in the links obtained from site

    # From stack overflow: ...some sites (including Wikipedia) block on common non-browser user agents strings, like the
    # "Python-urllib/x.y" sent by Python's libraries. Even a plain "Mozilla" or "Opera" is usually enough to bypass that
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent': user_agent,}
    for demdl in dl_links:
        # TODO: I changed the dl_links order so that it's easier to use later make sure it still works.
        try:
            # Download files until 4:30 (don't want to hog internet).
            if datetime.datetime.now().hour >= 16 and datetime.datetime.now().minute > 30:
                # Sleep until 12:30 am
                print('Sleeping... ' + datetime.datetime.now().strftime("%c"))
                time.sleep(8*60*60)  # sleep time in seconds (hours * mins * seconds)
                print('Back to work! ' + datetime.datetime.now().strftime("%c"))
            print('Downloading ' + demdl[1])
            url = site + demdl[2]
            req = urllib.request.Request(url, None, headers)
            dl = urllib.request.urlopen(req)
            # DL link is a redirect
            # Get the file name from the url and append ext id
            filename = demdl[2] + '_' + dl.geturl().split('/')[-1]
            with open(dl_location + filename, 'wb') as file:
                file.write(dl.read())
        except:
            print(["Issue during download", filename, url, req])
            # wait 2 minutes before trying again
            time.sleep(120)


if __name__ == '__main__':

    # print("Sleeping until 1 am on initial run.")
    # time.sleep(20000)
    # print("Getting up to work.")

    download_dems(find_demo_links(get_match_links(99)))
    hltv_unrar()

    call('C:\\Dropbox\\Dropbox\\HAXz\\PositionAnalyzer\\dem_utilities\\demo_parser\\CSPositionAnalyzer.exe D:\CSGOProGames\demos D:\CSGOProGames\processed')
    # If i get more storage, it would probably be useful to keep these files around (or the rar)
    # for dem in glob.glob('D:\\CSGOProGames\\demos\\*.dem'):
    #     os.remove(dem)

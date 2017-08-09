import requests
from bs4 import BeautifulSoup
import urllib
import random
import time
import datetime
import string
import MFLibrary.csv_functions

# used for external key generation
alphanums = string.ascii_letters + string.digits

def get_match_links(searchdepth, site='https://www.hltv.org'):
    """Gets all the links on the results page"""

    # Going to just increment the offset in the GET request in python rather than follow the url on the page
    offset = 0
    match_links = []

    while offset <= searchdepth: # get most recent 1000 matches ~3 mos worth
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
        if 'matches' in link:
            match_links.append(link)

    return match_links


# This could be refactored further.
def hltv_demscraper(match_links, site='https://www.hltv.org', dl_location='D:/CSGOProGames/rar/'):
    # exclude trailing / in site as it's included in the links obtained from site
    #
    # print("Sleeping until 1 am on initial run.")
    # time.sleep(20000)
    # print("Getting up to work.")

    # using underscore for readability
    dl_links = []
    hltv_links = []
    errors = []

    # following correct match links to find download links

    for link in match_links:
        req = requests.get("https://www.hltv.org{!s}".format(link))
        soup = BeautifulSoup(req.content, 'html.parser')
        # Get the download link from the match page and pair it with the match link for use by users to find exact games
        try:
            dl_links.append([soup.find_all('a', class_='flexbox left-right-padding')[0].get('href'), link]) # GOTV demo class
        except IndexError:
            # Sometimes matches don't have uploaded DEM files
            errors.append("Issue finding dem file (probably does not exist)", link, req)

    # From stack overflow: ...some sites (including Wikipedia) block on common non-browser user agents strings, like the
    # "Python-urllib/x.y" sent by Python's libraries. Even a plain "Mozilla" or "Opera" is usually enough to bypass that
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    headers = {'User-Agent': user_agent,}

    for demdl in dl_links:
        try:  # Keep chugging if there's an error
            ##
            ## Not going to use this today
            ##
            # # Download files from 1 am until noon while I'm away.
            # if datetime.datetime.now().hour > 12:
            #     # Sleep until
            #     print('Sleeping... ' + datetime.datetime.now().strftime("%c"))
            #     time.sleep(13*60*60) # sleep time in seconds (hours * mins * seconds)
            #     print('Back to work! ' + datetime.datetime.now().strftime("%c"))

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
            errors.append(["Issue during download", filename, url, req])
            # wait 2 minutes before trying again
            time.sleep(120)

    # Output key for external code to match link
    MFLibrary.csv_functions.writeListToCSV('D:/CSGOProGames/processed/!ExternalCodes.csv', hltv_links)
    # Output any encountered errors that were skipped
    MFLibrary.csv_functions.writeListToCSV(dl_location + '!Errors.csv', errors)

if __name__ == '__main__':
    hltv_demscraper()
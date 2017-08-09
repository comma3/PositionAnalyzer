from hltvscraper.hltv_scraper import *
from hltvunrar.hltv_unrar import *

from subprocess import call

hltv_demscraper(get_match_links(1000))
hltv_unrar()
call('C:\\Dropbox\\Dropbox\\HAXz\\PositionAnalyzer\\dem file utilities\\demo parser\\CSPositionAnalyzer.exe D:\\CSGOProGames\\demos D:\\CSGOProGames\\processed')





import os
import glob
# Download from http://www.rarlab.com/rar/UnRARDLL.exe
# Just including these here so I don't have to deal with this again
# Needs to be above import of unrar
os.environ['UNRAR_LIB_PATH'] = 'C:/Program Files (x86)/UnrarDLL/UnRAR.dll'
from unrar import rarfile


def hltv_unrar(dl_location, processed_location):

    if not os.path.exists(processed_location):
        os.mkdir(processed_location)

    for file in glob.glob(dl_location + '*.rar'):
        rar = rarfile.RarFile(file)
        rar.extractall(path=dl_location)
        extcode = file.split('\\')[-1].split('_')[0]
        dems = rar.namelist() #list of file names in archive (not including path)
        for dem in dems:
            os.rename(dl_location + dem, processed_location + extcode + '_' + dem)

if __name__ == '__main__':
    hltv_unrar('D:/CSGOProGames/!rarfiles/', 'D:/CSGOProGames/!demofiles/')
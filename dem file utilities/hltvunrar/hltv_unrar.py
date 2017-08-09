import os
import glob
# Download from http://www.rarlab.com/rar/UnRARDLL.exe
# Just including these here so I don't have to deal with this again
# Needs to be above import of unrar
os.environ['UNRAR_LIB_PATH'] = 'C:/Program Files (x86)/UnrarDLL/UnRAR.dll'
from unrar import rarfile


def hltv_unrar(dl_location='D:/CSGOProGames/!rarfiles/', processed_location='D:/CSGOProGames/!demofiles/'):

    if not os.path.exists(processed_location):
        os.mkdir(processed_location)

    for file in glob.glob(dl_location + '*.rar'):
        try:
            rar = rarfile.RarFile(file)
        except:
            print("++++++++++RAR ISSUE++++++++++")
            print(file)
            print("++++++++++RAR ISSUE++++++++++")
            continue
        rar.extractall(path=dl_location)
        extcode = file.split('\\')[-1].split('_')[0]
        dems = rar.namelist() #list of file names in archive (not including path)
        for dem in dems:
            if not os.path.exists(processed_location + extcode + '_' + dem):
                os.rename(dl_location + dem, processed_location + extcode + '_' + dem)
        # Delete rar when I'm done with it so I can hold more uncompressed dem files
        os.remove(file)

if __name__ == '__main__':
    hltv_unrar()
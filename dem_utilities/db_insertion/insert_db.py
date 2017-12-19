import MFLibrary as mf
import sqlite3
import csv
import glob

def GameDataImporter():

    # Connect to the DB
    conn = sqlite3.connect('D:\\CSGOProGames\\CSPAdb.sqlite3')
    curr = conn.cursor()

    numoffiles = 0

    gdmatch = 'a'
    pdmatch = 'b'
    ndmatch = 'c'
    mimatch = 'd'

    # Get csv files in folder
    for filename in glob.glob('D:\\CSGOProGames\\processed\\*.csv'):
        splitname = filename.split('_')
        # Make sure all three files are from the same match
        if splitname[-1] == 'extid.csv':
            matchcodedictionary = mf.csv.read_dictionary(filename)
        elif splitname[-1] == 'gamedata.csv':
            gamedatafile = filename
            gdmatch = splitname[0]  # Set these numbers to correct split number
        elif splitname[-1] == 'playerdata.csv':
            playerdatafile = filename
            pdmatch = splitname[0]
        elif splitname[-1] == 'nadedata.csv':
            nadedatafile = filename
            ndmatch = splitname[0]
        elif splitname[-1] == 'matchinfo.csv':
            matchinfofile = filename
            mimatch = splitname[0]
        else:
            print("Error in " + filename)
            continue


        #Make sure we have all three files and they are the same match
        if gdmatch == pdmatch == ndmatch == mimatch:
            numoffiles += 1
            print("Working on " + gdmatch)
            # Used to track round number. Data are divided into 'games' where each round is a game. However, data come in one input file.
            i = 0
            playerDataTupleList = []
            nadeDataTupleList = []
        else:
            # Go to next file. This approach keeps the indentation level lower
            continue

        # Open the files

        with open(gamedatafile) as gdf:
            with open(playerdatafile) as pdf:
                with open(nadedatafile) as ndf:

                    # Matchinfo only has one row but we can't subscript the csv.reader so we read it to a list
                    matchinfo = mf.csv.read_list(matchinfofile)

                    # We want these to be csv.reader objects so that they are destroyed as they are read
                    # (saves some time iterating or storing indices)
                    gamedata = csv.reader(gdf)
                    playerdata = csv.reader(pdf)
                    nadedata = csv.reader(ndf)

                    # We make a copy of player data to find bomb position (discussed below)
                    # iterate over these data when a bomb planted event is detected
                    bombdata = csv.reader(pdf)
                    try:
                        # Skip headers
                        next(playerdata)
                        next(gamedata)
                        next(nadedata)
                        next(bombdata)
                    except StopIteration:
                        # Data are missing TODO: Make sure these files don't get printed by demo parser
                        continue

                    # In the playerdata list, we don't know we've ended a round until we hit a row from the next
                    # Use this list to pass the data forward
                    carryrow = None

                    matchcode = matchinfo[1][0]
                    if matchcode != gdmatch.split('\\')[-1]:
                        print("Something seriously wrong happened. File names don't match game data.")
                    playedmap = matchinfo[1][1]
                    rank = matchinfo[1][2]
                    team1 = matchinfo[1][3]
                    team2 = matchinfo[1][4]
                    hltvlink = matchcodedictionary[matchcode]

                    try:
                        curr.execute("""INSERT INTO Analyzer_MatchInfo 
                                    (external_match_code, rank, team_1, team_2, hltv_link) 
                                    VALUES ('?', '?', '?', '?', '?')""",
                                     (matchcode, rank, team1, team2, hltvlink))

                        matchid = curr.lastrowid
                        conn.commit()

                    except sqlite3.IntegrityError:  # hltv link not unique
                        # This is fine. Files are separated by map but there can easily be multiple maps in a match
                        # TODO: Add some check at the beginning (when loading dictioary for first time) to remove files that may already be in db. This is redundant as the original download program should skip the intial download.
                        pass

                    # Prepare a game row and collect the gameid so it can be the foreign key for the player data
                    # Each gamerow is one round, the player data are all combined so they are separated below
                    for GameRow in gamedata:

                        firstroundtick = True # Test for first tick in a new file and store time - keep round times approximately the same from start rather than involving match times
                        ctscore = GameRow[3]
                        tscore = GameRow[4]
                        winreason = GameRow[5]

                        # gameinfo has to be done this way rather than as an array to get gameid
                        curr.execute("""INSERT INTO Analyzer_GameInfo 
                                    (match_id, played_map, t_score, ct_score, win_reason) 
                                    VALUES ('?', '?', '?', '?', '?')""",
                                    (matchid, playedmap, tscore, ctscore, winreason))

                        gameid = curr.lastrowid
                        conn.commit()  # Needs to be run to set gameid (was null without it)
                        #print("Game data committed")

                        i += 1  # Iterate round number
                        for PlayerRow in playerdata:

                            if int(PlayerRow[2]) == i:  # Round number = i

                                if firstroundtick:
                                    roundstarttime = float(PlayerRow[1])
                                    firstroundtick = False

                                if carryrow:
                                    playerDataTupleList.append(carryrow)
                                    carryrow = None

                                time = round(float(PlayerRow[1]) - roundstarttime, 1)
                                team = PlayerRow[5]
                                playernum = PlayerRow[6]
                                weapon = PlayerRow[15]

                                XPos = float(PlayerRow[7])
                                YPos = float(PlayerRow[8])
                                ZPos = float(PlayerRow[9])

                                playerDataTupleList.append((gameid, time, team, playernum, XPos, YPos, ZPos, weapon))

                            elif int(PlayerRow[2]) > i:
                                carryrow = (gameid, time, team, playernum, XPos, YPos, ZPos, weapon)
                                break

                        #print("Player data prepared")


                        for NadeRow in nadedata:

                            time = round(float(NadeRow[1]) - roundstarttime, 1)

                            if int(NadeRow[2]) == i: #find current round

                                # Csgo demo files do not report the bomb position directly
                                # So nade event has to be treated differently if it's a bomb plant
                                # Eventually need to include dropped bomb which isn't an event but will have to be found from player with bomb losing it from inventory or dying
                                #
                                # Bomb event may have player attached which could simplify code below
                                #
                                # Also note that fire nades do not include the thrower, so that information will have to be obtained in the same way as bomb drops
                                # This feature is not implemented now and likely is not important, but leaving this note in case it does become important
                                #
                                if NadeRow[6] == 'Bomb Planted':

                                    for BombRow in bombdata: # Have to iterate over player data to find bomb plant position

                                        if int(BombRow[2]) == i and time >= float(BombRow[1]) - roundstarttime > time-1 and 'Bomb' == BombRow[15]: #finds player with bomb as active weapon within a few seconds of bomb plant. Range was expanded to reduce time incongruity errors. These errors may have been resolved. SHould test in next batch.
                                            nadetype = 'BombPlanted'
                                            XPos = float(BombRow[7])
                                            YPos = float(BombRow[8])
                                            ZPos = float(BombRow[9])
                                            break
                                        elif int(BombRow[2]) > i: # Missed bomb plant somehow - knife rounds seem to cause this for some reason
                                            nadetype = 'Error'
                                            XPos = 0
                                            YPos = 0
                                            ZPos = 0
                                            break
                                else:
                                    nadetype = NadeRow[6]

                                    XPos = float(NadeRow[7])
                                    YPos = float(NadeRow[8])
                                    ZPos = float(NadeRow[9])

                                nadeDataTupleList.append((gameid, time, nadetype, XPos, YPos, ZPos))

                            elif int(NadeRow[2]) > i:  # Stop searching if we go to far
                                break

                        # print("Nade data prepared")

                    curr.executemany("""INSERT INTO Analyzer_PlayerData
                                    (game_id, time, team, playernum, XPos, YPos, ZPos, weapon) 
                                    VALUES (?,?,?,?,?,?,?,?)  """, playerDataTupleList)

                    curr.executemany("""INSERT INTO Analyzer_Nades 
                                    (game_id, time, nade_type, XPos, YPos, ZPos) 
                                    VALUES (?,?,?,?,?,?)  """, nadeDataTupleList)

                    conn.commit()

                    gdmatch = 'a'
                    pdmatch = 'b'
                    ndmatch = 'c'
                    mimatch = 'd'



    conn.close()
    print("Finished! {} files were added to the database.".format(numoffiles))


if __name__ == '__main__':
    GameDataImporter()
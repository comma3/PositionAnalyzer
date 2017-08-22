import operator
from functools import reduce

from django.db.models import Q, F
from django.shortcuts import render
from django.http import JsonResponse


import munkres
import numpy as np
import pandas as pd
import sqlite3

def find_games(request):

    data = {
        'ctkills': 1,
        'defuse': 2,
        'time': 3,
        'tkills': 4,
        'bombed': 5,
    }

    game_objects = request.POST.get('gameobjects', None).split('_')
    request_map = request.POST.get('map', None)

    # Organize and cleaning the input
    pieces =[]
    for object in game_objects :
        piece = object.split('-')
        coords = piece.pop().split(',')
        piece.extend(coords)
        pieces.append([x.strip() for x in piece])

    players = []
    nades = []
    for piece in pieces:
        if 'T' in piece[0]:
            players.append(piece)
        else:
            nades.append(piece)

    # Update these from website later
    threshold = 0.85
    distance_scale = 2000.0  # took out square root in measurement so this should be units^2
    nade_range = 2

    if request_map.lower() == 'inferno':
        xoffset = 1760.0
        yoffset = 790.0

    conn = sqlite3.connect('/vagrant/data/CSPAdb.sqlite3')
    match_links = pd.read_sql_query("""SELECT id,hltv_link FROM analyzer_MatchInfo""", conn)

    playerdata = pd.read_sql_query("""SELECT time, team, XPos, YPos, weapon, game_id, t_score, ct_score, win_reason, match_id
                                FROM analyzer_PlayerData
                                JOIN analyzer_GameInfo 
                                ON analyzer_PlayerData.game_id = analyzer_GameInfo.id
                                WHERE played_map = 'inferno'
                                LIMIT 150000""", conn)

    # Nades have different time stamps
    nade_data = pd.read_sql_query("""SELECT time, XPos, YPos, nade_type, game_id
                            FROM analyzer_Nades
                            JOIN analyzer_GameInfo 
                            ON analyzer_Nades.game_id = analyzer_GameInfo.id
                            WHERE played_map = 'inferno'
                            LIMIT 150000""", conn)
    conn.close()

    bytick = playerdata.groupby(['game_id', 'time'])

    matching_games = []
    matches = set()

    for tick in bytick:
        tick = tick[1]  # Tick gives a tuple of ((time, game), dataframe)
        # Already included this game.
        if tick.iloc[0]['game_id'] in matches:
            continue

        nade_similarity = 0
        player_similarity = 0

        if players:
            similarities = []
            # We need to go through the entire tick before we know how many living players there are
            dead_T = 5
            dead_CT = 5
            wanted_dead_T = 0
            wanted_dead_CT = 0
            for i, player_row in tick.iterrows():
                tempscore = []

                if player_row['team'] == 'T':
                    dead_T -= 1
                elif player_row['team'] == 'CT':
                    dead_CT -= 1

                for player in players:
                    score = 0.0
                    if player[0] == 'T' and player[1] == 'Dead':
                        tempscore.append('DT')
                        wanted_dead_T += 1
                        continue
                    elif player[0] == 'CT' and player[1] == 'Dead':
                        tempscore.append('DCT')
                        wanted_dead_CT += 1
                        continue

                    if player_row['team'] == player[0]:
                        if player[1] == player_row['weapon'] or player[1] == 'Any':
                            score += 1
                        distance = ((player_row['XPos'] + xoffset) - (player[2] * 9.75)) ** 2 + (
                        (player_row['YPos'] + yoffset) - (player[3] * 9.75)) ** 2
                        score += 2 ** -(distance / distance_scale)
                        tempscore.append(score)
                    else:
                        tempscore.append(0)
                similarities.append(tempscore)

                # This seems ot make the code slower somehow? ~40 s vs ~60 s
                # Skip ahead because this tick is very unlikely to have a high similarity score
                #         if wanted_dead_T/len(tick.index) > dead_T or wanted_dead_CT/len(tick.index) > dead_CT:
                #             continue

            colmaxes = []
            for i, row in enumerate(similarities):
                for j, column in enumerate(row):
                    if column == 'DCT':
                        if dead_CT > 0:
                            similarities[i][j] = 2  # Determine good value
                        else:
                            similarities[i][j] = 0
                    elif column == 'DT':
                        if dead_T > 0:
                            similarities[i][j] = 2
                        else:
                            similarities[i][j] = 0
                    try:
                        if colmaxes[j] < similarities[i][j]:
                            colmaxes[j] = similarities[i][j]
                    except:
                        colmaxes.append(0)
                    # Turn profit function into cost function
                    similarities[i][j] = 2.0 - similarities[i][j]

            if sum(colmaxes) / (len(players) * 2) < threshold:  # Have to the possibility of exceeding the threshold
                continue

            # Assignment problem : https://en.wikipedia.org/wiki/Assignment_problem
            # Solved in O(n^3) using this algorithm
            # http://software.clapper.org/munkres/
            # This algorithm uses a cost calculation (i.e., minimization)
            # so we first need to subtract the values from the max value
            # (performed during dead player value assignment)

            player_similarity = 0
            if similarities:
                m = munkres.Munkres()
                indices = m.compute(similarities)
                for row, column in indices:
                    # Revert to a similarity (high is better) and calculat total
                    player_similarity += 2.0 - similarities[row][column]

        if nades:
            similarities = []
            nade_similarity = 0
            # Get all the nades from the same game within a defined time range.

            nade_rows = nade_data.loc[
                (nade_data.time < player_row.time + nade_range) & (nade_data.time > player_row.time - nade_range) & (
                nade_data.game_id == player_row.game_id)]
            if len(nade_rows.index) >= len(nades):
                for i, nade_row in nade_rows.iterrows():
                    tempscore = []
                    for nade in nades:
                        score = 0.0
                        if nade_row['nade_type'] == nade[0]:
                            # Customized for each map
                            distance = ((nade_row['XPos'] + xoffset) - (nade[1] * 9.75)) ** 2 + ((nade_row['YPos'] + yoffset) - (nade[2] * 9.75)) ** 2
                            score += 2 ** -(distance / distance_scale)  # Approaches 1 as distance decreases
                            tempscore.append(score)
                        else:
                            tempscore.append(0)

                    similarities.append(tempscore)

                for i, row in enumerate(similarities):
                    for j, column in enumerate(row):
                        # Turn profit function into cost function
                        similarities[i][j] = 1 - similarities[i][j]

                if similarities:
                    m = munkres.Munkres()
                    indices = m.compute(similarities)
                    for row, column in indices:
                        # Revert to a similarity (high is better) and calculate total
                        nade_similarity += 1 - similarities[row][column]

        total_similarity = (float(player_similarity) + float(nade_similarity)) / ((2 * len(players)) + len(nades))  # Weighted normalization

        if total_similarity > threshold:
            print(total_similarity, player_similarity, nade_similarity)
            matching_games.append([total_similarity, player_row['win_reason'],
                                   match_links.loc[(match_links.id == player_row.match_id)]['hltv_link'],
                                   player_row['t_score'], player_row['ct_score']])
            matches.add(player_row['game_id'])

    data = {'results' : matching_games}

    return JsonResponse(data)

def show_site(request):

    return render(request, 'analyzer/analyzer.html')
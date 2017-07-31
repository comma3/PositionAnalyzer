import operator
from functools import reduce

from analyzer.models import PlayerData, Nades
from django.db.models import Q, F
from django.shortcuts import render

precision = {"exact": 0, "tight": 1, "loose" : 2}


def dbquery(request):


    Error = 'false'
    TPosIn = []
    CTPosIn = []
    TPos = []
    CTPos = []
    NadeList = []

    #Get data from website

    nades = request.POST.get('nadesbox', 'nope').replace("-", "").split()
    if len(nades) >= 3:
        for entry in nades:
            NadeTemp = []
            for i in range(0,3):
                NadeTemp.append(nades.pop())
            NadeList.append(NadeTemp)


    #throwerror = int("blah")

    #put all data into arrays excluding errors and 'Any'
    for i in range(1,5):
        TPosTemp = request.POST.get('T'+str(i)+'Status', 'nope')
        if TPosTemp != 'nope' and TPosTemp != 'Any':
            TPosIn.append(TPos)
            TPosIn.append(request.POST.get('T'+str(i)+'precision', 'nope'))
            TPos.append(TPosIn)
        CTPosTemp = request.POST.get('CT'+str(i)+'Status', 'nope')
        if CTPosTemp != 'nope' and CTPosTemp != 'Any':
            CTPosIn.append(CTPosTemp)
            CTPosIn.append(request.POST.get('CT'+str(i)+'precision', 'nope'))
            CTPos.append(CTPosIn)
        if TPosTemp == 'nope' or CTPosTemp == 'nope':
            Error = 'true'
            break



 #Javascript does some checks prior to submitting query. Hopefully that will decrease server load. This should still trigger if the JS allows impossible searches through.
    if len(CTPos) == 0 and len(TPos) == 0 and len(NadeList) == 0 or Error == True:
        return render(request, 'analyzer/analyzer.html', {'Error' : Error, 'BadSearch' : 'true', 'NoGames' : 'false', 'CTKill': 1, 'TKill' : 2, 'Defuse': 1, 'Time' : 1,'TargetBombed': 1})


    if len(CTPos) > 0 or len(TPos) > 0 or len(nades) > 0:

        query = []

        for pos in CTPos:
            xcoord = int(pos[0].split(',')[0])
            ycoord = int(pos[0].split(',')[1])

            XMax = (xcoord+precision[pos[1]])*39-1760
            XMin = (xcoord-precision[pos[1]]-1)*39-1760
            YMax = (ycoord+precision[pos[1]])*39-790
            YMin = (ycoord-precision[pos[1]]-1)*39-790

            query.append(Q(XPos__lte = XMax) & Q(XPos__gt = XMin) & Q(YPos__lte = YMax) & Q(YPos__gt = YMin))

        #ctsearch =  PlayerData.objects.filter(Q(team = "CounterTerrorist"), reduce(operator.or_, query)).groupby(time, game).count().filter(count__lt = len(querylen)) #general idea of how this needs to be accomplished
        ctsearch =  PlayerData.objects.filter(Q(team = "CounterTerrorist"), reduce(operator.or_, query)).annotate(time = 'time', games = 'game') #general idea of how this needs to be accomplished

        timeinterval = ctsearch.filter(game = F('game'), time = F('time'))

        for pos in TPos:
            xcoord = int(pos[0].split(',')[0])
            ycoord = int(pos[0].split(',')[1])

            XMax = (xcoord+precision[pos[1]])*39-1760
            XMin = (xcoord-precision[pos[1]]-1)*39-1760
            YMax = (ycoord+precision[pos[1]])*39-790
            YMin = (ycoord-precision[pos[1]]-1)*39-790

            query.append(Q(XPos__lte = XMax) & Q(XPos__gt = XMin) & Q(YPos__lte = YMax) & Q(YPos__gt = YMin))

        tsearch =  PlayerData.objects.filter(Q(team = "Terrorist"), reduce(operator.or_, query)).values('time', 'game')

        #Nade array comes in different order than player arrays for UI
        #Precision, coords, type
        for pos in NadeList:
            xcoord = int(pos[1].split(',')[0])
            ycoord = int(pos[1].split(',')[1])

            XMax = (xcoord+precision[pos[0]])*39-1760
            XMin = (xcoord-precision[pos[0]]-1)*39-1760
            YMax = (ycoord+precision[pos[0]])*39-790
            YMin = (ycoord-precision[pos[0]]-1)*39-790

            query.append(Q(XPos__lte = XMax) & Q(XPos__gt = XMin) & Q(YPos__lte = YMax) & Q(YPos__gt = YMin) & Q(nade_type = pos[2]))

        nadesearch = Nades.objects.filter(reduce(operator.or_, query)).values('time', 'game')


        if ctsearch.count() == 0 and tsearch.count() == 0 and nadesearch.count() == 0:
            return render(request, 'analyzer/analyzer.html', {'Error' : Error, 'BadSearch' : 'false', 'NoGames' : 'true', 'CTKill': 0, 'TKill' : 0, 'Defuse': 0, 'Time' : 0,'TargetBombed': 1})

        #need to rewrite queries above. don't know if I can combine the query sets

        DefuseCount = ctsearch.filter(game_id__win_reason='BombDefused').count() #not sure what real word is
        #I think the above line is correct based on use in shell

        TimeCount = ctsearch.filter(game_id__win_reason='TargetSaved').count() #not sure what real word is
        CTKillCount = ctsearch.filter(game_id__win_reason='CTWin').count()

        TKillCount = ctsearch.filter(game_id__win_reason='TerroristWin').count()
        BombCount = ctsearch.filter(game_id__win_reason='TargetBombed').count()


        return render(request, 'analyzer/analyzer.html', {'Error' : Error,  'CTKill': CTKillCount, 'TKill' : TKillCount, 'Defuse': DefuseCount, 'Time' : TimeCount,'TargetBombed': BombCount})

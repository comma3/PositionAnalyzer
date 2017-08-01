from django.db import models

class MatchInfo(models.Model):

    external_match_code = models.CharField(max_length=20)
    played_map = models.CharField(max_length=20)
    rank = models.IntegerField()
    team_1 = models.CharField(max_length=40)
    team_2 = models.CharField(max_length=40)
    hltv_link = models.CharField(max_length=100, unique=True) #want to ensure that DB doesn't include duplicates

    def __str__(self):
        return self.played_map + ' - ' + self.team_1 + ' - ' + self.team_2

class GameInfo(models.Model):

    match = models.ForeignKey(MatchInfo, on_delete=models.CASCADE)
    t_score = models.IntegerField()
    ct_score = models.IntegerField()
    win_reason = models.CharField(max_length=20) #win_reason contains the winning team, so the winner might be unnecessary information

    def __str__(self):
        return self.played_map + ' - ' + self.win_reason


class PlayerData(models.Model):

    game = models.ForeignKey(GameInfo, on_delete=models.CASCADE)
    time = models.DecimalField(max_digits=6, decimal_places=4) #This time comes when on tick intervals (1/16 currently or 0.5s), so they do not match PlayerData time stamps, which log times when nades are thrown.
    team = models.CharField(max_length=20)
    playernum = models.IntegerField()
    XPos = models.DecimalField(max_digits=6, decimal_places=4)
    YPos = models.DecimalField(max_digits=6, decimal_places=4)
    ZPos = models.DecimalField(max_digits=6, decimal_places=4)
    weapon = models.CharField(max_length=20)


class Nades(models.Model):

    game = models.ForeignKey(GameInfo, on_delete=models.CASCADE)
    time = models.DecimalField(max_digits=6, decimal_places=4) #This time comes as an event when the nades explode not on a tick interval, so they do not match PlayerData time stamps
    XPos = models.DecimalField(max_digits=6, decimal_places=4)
    YPos = models.DecimalField(max_digits=6, decimal_places=4)
    ZPos = models.DecimalField(max_digits=6, decimal_places=4)
    nade_type = models.CharField(max_length=15)



#I'm not sure whether this info is useful or not.
#Consider including team names in here
#Try to differentiate Pro tiers at that time
#class PlayerInfo(models.Model):
#    game_id = models.ForeignKey(GameInfo, on_delete=models.CASCADE)
#    SteamIDPlayer1 = models.CharField(max_length=30)


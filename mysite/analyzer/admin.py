from django.contrib import admin
from analyzer.models import GameInfo, PlayerData, Nades



    


admin.site.register(GameInfo)
admin.site.register(PlayerData)
admin.site.register(Nades)





#This shit don't work
#from import_export import resources
#from import_export.admin import ImportExportModelAdmin
#
#
#
#class GameInfoResource(resources.ModelResource):
#
#    class Meta:
#        model = GameInfo
#        skip_unchanged = True
#        report_skipped = False
#
#
#class PlayerDataResource(resources.ModelResource):
#    
#    class Meta:
#        model = PlayerData
#        skip_unchanged = True
#        report_skipped = False
#        
#   
#
#class GameInfoAdmin(ImportExportModelAdmin):
#    resource_class = GameInfoResource
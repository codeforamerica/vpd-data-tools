from django.contrib.gis import admin

from rms.models import Incident, Incunit, GPSLog

class IncunitInline(admin.TabularInline):
    model = Incunit
    readonly_fields = (
        'incident',
        'unitid',
        'ofcrnum',
        'dispdatetime',
        'enrtdatetime',
        'osdatetime',
        'cleardatetime',
        'primaryunit'
    )
    extra = 0

class IncidentAdmin(admin.ModelAdmin):
    readonly_fields = (
        'incnum',
        'type',
        'location',
        'num',
        'street',
        'status',
        'cname',
        'cadrs',
        'capt',
        'cphone',
        'pu',
        'timestamp',
        'beat',
        'casen',
        'rcvtime',
        'disptime',
        'enrttime',
        'ostime',
        'cleartime',
        'cmt1'
    )

    list_display = ('incnum', 'type', 'location', 'timestamp', 'rcvtime', 'disptime', 'enrttime', 'ostime', 'cleartime')

    inlines = [IncunitInline,]

class GPSLogAdmin(admin.OSMGeoAdmin):
    readonly_fields = (
        'unitid',
        # 'location',
        'timestamp',
        'heading',
        'speed',
        'status'
    )
    modifiable = False

    list_display = ['unitid', 'timestamp', 'heading', 'speed', 'status']

admin.site.register(Incident, IncidentAdmin)
admin.site.register(GPSLog, GPSLogAdmin)

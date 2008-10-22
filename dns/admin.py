##
##
##
from django.contrib import admin
from noc.dns.models import DNSServer,DNSZoneProfile,DNSZone,DNSZoneRecordType,DNSZoneRecord

class DNSServerAdmin(admin.ModelAdmin):
    list_display=["name","generator_name","ip","location","description"]
    search_fields=["name","description","ip"]
    list_filter=["generator_name"]
    
class DNSZoneProfileAdmin(admin.ModelAdmin):
    pass

class DNSZoneRecordInline(admin.TabularInline):
    model=DNSZoneRecord
    extra=3
    
class DNSZoneAdmin(admin.ModelAdmin):
    inlines=[DNSZoneRecordInline]
    list_display=["name","description","is_auto_generated","serial","distribution"]
    list_filter=["is_auto_generated"]
    search_fields=["name","description"]
    
class DNSZoneRecordTypeAdmin(admin.ModelAdmin):
    list_display=["type","is_visible"]
    search_fields=["type"]
    list_filter=["is_visible"]

admin.site.register(DNSServer, DNSServerAdmin)
admin.site.register(DNSZoneProfile,DNSZoneProfileAdmin)
admin.site.register(DNSZone,DNSZoneAdmin)
admin.site.register(DNSZoneRecordType,DNSZoneRecordTypeAdmin)

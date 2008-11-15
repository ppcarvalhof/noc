from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from noc.dns.views import zone,zone_rpsl

urlpatterns = patterns ( "",
    (r"(?P<zone>[a-zA-Z0-9\-.]+)/zone/(?P<ns_id>\d+)/",         login_required(zone)),
    (r"(?P<zone>[a-zA-Z0-9\-.]+)/zone/rpsl/",                   login_required(zone_rpsl)),
)

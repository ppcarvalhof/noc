# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## DLink.DxS.get_local_users test
## Auto-generated by manage.py debug-script at 2011-03-29 12:16:35
##----------------------------------------------------------------------
## Copyright (C) 2007-2011 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------
from noc.lib.test import ScriptTestCase
class DLink_DxS_get_local_users_Test(ScriptTestCase):
    script="DLink.DxS.get_local_users"
    vendor="DLink"
    platform='DGS-3120-24TC'
    version='1.01.B033'
    input={}
    result=[{'class': 'superuser', 'is_active': True, 'username': 'kadm'}]
    motd='**********\n\n'
    cli={
## 'disable clipaging'
'disable clipaging': """disable clipaging
Command: disable clipaging

Success.                                                          
""", 
## 'show account'
'show account': """show account
Command: show account

 Current Accounts:
 Username             Access Level
 ---------------      ------------
 kadm                 Admin       

 Total Entries : 1
""", 
}
    snmp_get={}
    snmp_getnext={}

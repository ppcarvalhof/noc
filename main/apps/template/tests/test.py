# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## main.template unittes
##----------------------------------------------------------------------
## Copyright (C) 2007-2012 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------

## NOC modules
from noc.lib.test import RestModelTestCase, unittest

@unittest.skip("Not ready")
class PyRuleTestCase(RestModelTestCase):
    app = "main.template"

    scenario = [
        {
            "GET": {
                # key: value
            },
            "POST": {
                # key: value
            },
            "PUT": {
                # key: value
            }
        }
    ]


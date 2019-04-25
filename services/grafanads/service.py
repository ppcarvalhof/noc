#!./bin/python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# GrafanaDS service
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from __future__ import absolute_import
# NOC modules
from noc.core.service.ui import UIService
from .check import CheckHandler
from .annotations import AnnotationsHandler


class GrafanaDSService(UIService):
    name = "grafanads"

    def get_handlers(self):
        return super(GrafanaDSService, self).get_handlers() + [
            ("^/api/grafanads/annotations", AnnotationsHandler, {"service": self}),
            ("^/api/grafanads/", CheckHandler)
        ]


if __name__ == "__main__":
    GrafanaDSService().start()

# ---------------------------------------------------------------------
# Cisco.AireOS.get_version
# ---------------------------------------------------------------------
# Copyright (C) 2007-2009 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetversion import IGetVersion

rx_ver = re.compile(r"^Product Version\.+\s+(?P<version>\S+)", re.MULTILINE | re.DOTALL)
rx_inv = re.compile(r"^PID:\s+(?P<platform>\S+)", re.MULTILINE | re.DOTALL)


class Script(BaseScript):
    name = "Cisco.AireOS.get_version"
    cache = True
    interface = IGetVersion

    def execute(self):
        v = self.cli("show sysinfo")
        match = rx_ver.search(v)
        version = match.group("version")
        v = self.cli("show inventory")
        match = rx_inv.search(v)
        platform = match.group("platform")
        return {"vendor": "Cisco", "platform": platform, "version": version}

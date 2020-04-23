# ---------------------------------------------------------------------
# H3C.VRP.get_vlans
# ---------------------------------------------------------------------
# Copyright (C) 2007-2011 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC Modules
from noc.sa.profiles.Generic.get_vlans import Script as BaseScript
from noc.sa.interfaces.igetvlans import IGetVlans


class Script(BaseScript):
    name = "H3C.VRP.get_vlans"
    interface = IGetVlans

    rx_vlan_line_vrp3 = re.compile(
        r"^\sVLAN ID:\s+?(?P<vlan_id>\d{1,4})\n.*?Name:\s+(?P<name>.*?)\n.*?" r"(\n\n|$)",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )

    def execute_cli(self, **kwargs):
        vlans = self.cli("display vlan all")
        return [
            {"vlan_id": int(match.group("vlan_id")), "name": match.group("name")}
            for match in self.rx_vlan_line_vrp3.finditer(vlans)
        ]

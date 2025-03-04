# ---------------------------------------------------------------------
# HP.ProCurve.get_interfaces
# ---------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetinterfaces import IGetInterfaces
from noc.core.ip import IPv4


class Script(BaseScript):
    name = "HP.ProCurve.get_interfaces"
    interface = IGetInterfaces

    iftypes = {
        "6": "physical",
        "161": "aggregated",
        "54": "aggregated",
        "53": "SVI",
        "24": "loopback",
    }

    objstr = {
        "ifName": "name",
        "ifDescr": "description",
        "ifPhysAddress": "mac",
        "ifType": "type",
        "ifAdminStatus": "admin_status",
        "ifOperStatus": "oper_status",
        "ifAlias": "description",
    }

    rx_ip = re.compile(
        r"\s+(?P<name>\S+)\s+\|\s+(Manual|Disabled)\s"
        r"+(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s"
        r"+(?P<mask>\d{1,3}.\d{1,3}\.\d{1,3}\.\d{1,3})"
    )

    def execute(self):
        iface = {}
        interfaces = []
        step = len(self.objstr)
        lines = self.cli("walkMIB " + " ".join(self.objstr)).split("\n")[:-1]
        sh_ip = self.cli("show ip")

        try:
            sh_ospf = self.cli("show ip ospf interface")
        except Exception:
            sh_ospf = False

        portchannel_members = {}  # member -> (portchannel, type)

        for pc in self.scripts.get_portchannel():
            i = pc["interface"]
            t = pc["type"] == "L"
            for m in pc["members"]:
                portchannel_members[m] = (i, t)

        switchports = {}
        vlans = self.scripts.get_vlans()
        if vlans:
            for sp in self.scripts.get_switchport():
                switchports[sp["interface"]] = (
                    sp["untagged"] if "untagged" in sp else None,
                    sp["tagged"],
                )

        i = 0
        for s in range(int(len(lines) / step)):
            for str in lines[i : i + step]:
                leaf = str.split(".")[0]
                val = str.split("=")[1].lstrip()
                if leaf == "ifPhysAddress":
                    if not val:
                        continue
                    iface[self.objstr[leaf]] = val.rstrip().replace(" ", ":")
                elif leaf == "ifType":
                    iface[self.objstr[leaf]] = self.iftypes[val]
                elif leaf[-6:] == "Status":
                    iface[self.objstr[leaf]] = val == "1"
                elif leaf == "ifAlias":
                    # IF-MIB::ifName.1 = STRING: A1
                    # IF-MIB::ifName.2 = STRING: A2
                    # IF-MIB::ifName.3 = STRING: A3
                    #
                    # IF-MIB::ifDescr.1 = STRING: A1
                    # IF-MIB::ifDescr.2 = STRING: A2
                    # IF-MIB::ifDescr.3 = STRING: A3
                    if iface["name"] == iface["description"]:
                        iface["description"] = val
                else:
                    iface[self.objstr[leaf]] = val
            ifname = iface["name"]
            sub = iface.copy()
            ifindex = str.split("=")[0].split(".")[1].rstrip()
            iface["snmp_ifindex"] = int(ifindex)
            sub["snmp_ifindex"] = int(ifindex)
            sub["enabled_afi"] = []
            del sub["type"]

            for line in sh_ip.split("\n"):
                match = self.rx_ip.search(line)
                if match:
                    if match.group("name") == sub["name"]:
                        sub["enabled_afi"] += ["IPv4"]
                        sub["ipv4_addresses"] = [
                            IPv4(match.group("ip"), netmask=match.group("mask")).prefix
                        ]
                        if sh_ospf:
                            for o in sh_ospf.split("\n"):
                                if o.split():
                                    if o.split()[0] == match.group("ip"):
                                        sub["is_ospf"] = True
            if ifname in switchports and ifname not in portchannel_members:
                sub["enabled_afi"] += ["BRIDGE"]
                u, t = switchports[ifname]
                if u:
                    sub["untagged_vlan"] = u
                if t:
                    sub["tagged_vlans"] = t

            iface["subinterfaces"] = [sub]
            interfaces += [iface]
            iface = {}
            i = i + step
        return [{"interfaces": interfaces}]

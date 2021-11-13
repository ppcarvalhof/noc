# ---------------------------------------------------------------------
# Vendor: Raisecom
# OS:     ROS
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.profile.base import BaseProfile
from noc.core.confdb.syntax.patterns import ANY


class Profile(BaseProfile):
    name = "Raisecom.ROS"
    pattern_unprivileged_prompt = rb"^\S+?>"
    command_super = "enable"
    pattern_prompt = rb"^\S+?#"
    command_exit = "exit"
    pattern_more = [(rb"^ --More--\s*", b" ")]
    pattern_syntax_error = rb"(% \".+\"  (?:Unknown command.)|Error input in the position marke[dt] by|%\s+Incomplete command\.)"
    pattern_operation_error = rb"% You Need higher priority!"
    rogue_chars = [re.compile(rb"\x08+\s+\x08+"), b"\r"]
    config_volatile = [
        r"radius(-server | accounting-server |-)encrypt-key \S+\n",
        r"tacacs(-server | accounting-server |-)encrypt-key \S+\n",
    ]
    config_tokenizer = "context"
    config_tokenizer_settings = {
        "line_comment": "!",
        "contexts": [["interface", ANY, ANY]],
        "end_of_context": "!",
    }
    collators = ["noc.core.confdb.collator.ifname.IfNameCollator"]

    matchers = {
        "is_iscom2624g": {"platform": {"$regex": r"ISCOM26(?:24|08)G"}},
        "is_rotek": {"vendor": {"$in": ["Rotek", "ROTEK"]}},
        "is_gazelle": {"platform": {"$regex": r"^[SR]\d+[Ii]\S+"}},
        "is_ifname_use": {"platform": {"$regex": "QSW-8200"}},
    }

    rx_port = re.compile(r"^[Pp]ort(|\s+)(?P<port>\d+)")  # Port1-FastEthernet,port 1
    rx_port_ip = re.compile(r"^(IP|ip interface)(|\s+)(?P<port>\d+)")  # ip interface 0, IP0

    def convert_interface_name(self, interface):
        if interface.startswith("GE"):
            return interface.replace("GE", "gigaethernet")
        if interface.startswith("FE"):
            return interface.replace("FE", "fastethernet")
        if self.rx_port.match(interface):
            match = self.rx_port.match(interface)
            return match.group("port")
        if self.rx_port_ip.match(interface):
            match = self.rx_port_ip.match(interface)
            return "ip %s" % match.group("port")
        else:
            return interface

    INTERFACE_TYPES = {
        "nu": "null",  # NULL
        "fa": "physical",  # fastethernet
        "fe": "physical",  # fastethernet
        "gi": "physical",  # gigaethernet
        "ge": "physical",  # gigaethernet
        "lo": "loopback",  # Loopback
        "tr": "aggregated",  #
        "po": "aggregated",  # port-channel
        "mn": "management",  # Stack-port
        # "te": "physical",  # TenGigabitEthernet
        "vl": "SVI",  # vlan
        "ip": "SVI",  # IP interface
        "un": "unknown",
    }

    @classmethod
    def get_interface_type(cls, name):
        if name == "fastethernet1/0/1":
            # for ISCOM26(?:24|08)G
            # @todo use matchers
            return "management"
        elif name.isdigit():
            return "physical"
        return cls.INTERFACE_TYPES.get(name[:2].lower())

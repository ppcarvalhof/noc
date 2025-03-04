# ---------------------------------------------------------------------
# Eltex.MES.get_inventory
# ---------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetinventory import IGetInventory
from noc.core.text import parse_table
from noc.core.validators import is_int


class Script(BaseScript):
    name = "Eltex.MES.get_inventory"
    interface = IGetInventory
    cache = True

    rx_hardware = re.compile(r"^HW version+\s+(?P<hardware>\S+)$", re.MULTILINE)
    rx_serial1 = re.compile(r"^Serial number :\s+(?P<serial>\S+)$", re.MULTILINE)
    rx_serial2 = re.compile(r"^\s+1\s+(?P<serial>\S+)\s*\n", re.MULTILINE)
    rx_serial3 = re.compile(
        r"^\s+1\s+(?P<mac>\S+)\s+(?P<hardware>\S+)\s+(?P<serial>\S+)\s*\n", re.MULTILINE
    )
    rx_platform = re.compile(r"^System Object ID:\s+(?P<platform>\S+)$", re.MULTILINE)
    rx_descr = re.compile(r"^System (?:Description|Type):\s+(?P<descr>.+)$", re.MULTILINE)
    rx_pwr = re.compile(
        r"^(?P<type>\S+) Power Supply Status \[(?P<pwr_type>\S+)\]:\s+", re.MULTILINE
    )
    rx_trans = re.compile(
        r"^\s*Transceiver information:\s*\n"
        r"^\s*Vendor name: (?P<vendor>.+?)\s*\n"
        r"^\s*Serial number: (?P<serial>.+?)\s*\n"
        r"(^\s*Part number: (?P<part_no>.+?)\s*\n)?"
        r"(^\s*Vendor revision: (?P<revision>.+?)\s*\n)?"
        r"^\s*Connector type: (?P<conn_type>.+?)\s*\n"
        r"^\s*Type: (?P<type>.+?)\s*\n"
        r"^\s*Compliance code: (?P<code>.+?)\s*\n"
        r"^\s*Laser wavelength: (?P<wavelength>.+?)\s*\n"
        r"^\s*Transfer distance: (?P<distance>.+?)\s*\n",
        re.MULTILINE,
    )
    has_detail = True

    def get_chassis(self, plat, ver, ser, unit: int = None):
        match = self.rx_descr.search(plat)
        if match and match.group("descr").startswith("MES"):
            descr = match.group("descr")
        else:
            descr = None

        platform, revision = None, None
        match = self.rx_platform.search(plat)
        if match:
            platform = match.group("platform")
            platform = platform.split(".")[8]
            platform, revision = self.profile.get_platform(platform)
        elif self.has_capability("Stack | Members"):
            # Try to obtain platform from description
            if descr and descr.startswith("MES"):
                platform = descr.split()[0]  # MES-3124F
                if not descr.startswith("MES-"):  # MES2208P
                    platform = "MES-%s" % platform[3:]

        hardware = self.rx_hardware.search(ver)

        match = self.rx_serial1.search(ser)
        match2 = self.rx_serial3.search(ser)
        if match:
            serial = self.rx_serial1.search(ser)
        elif match2:
            # Unit    MAC address    Hardware version Serial number
            # ---- ----------------- ---------------- -------------
            # 1   xx:xx:xx:xx:xx:xx     02.01.02      ESXXXXXXX
            serial = self.rx_serial3.search(ser)
        else:
            serial = self.rx_serial2.search(ser)

        r = {"type": "CHASSIS", "vendor": "ELTEX", "part_no": [platform]}
        if serial:
            r["serial"] = serial.group("serial")
        if revision:
            r["revision"] = revision.split(".")[-1]
        elif hardware:
            r["revision"] = hardware.group("hardware")
        if descr:
            r["description"] = descr
        if unit:
            r["number"] = unit
        return r

    def get_pwr(self, type, pwr_type, platform):
        if platform in [
            "MES-3108",
            "MES-3108F",
            "MES-3116",
            "MES-3116F",
            "MES-3124",
            "MES-3124F",
            "MES-3308F",
            "MES-3316F",
            "MES-3324",
            "MES-3324F",
            "MES-3348",
            "MES-3348F",
            "MES-5312",
            "MES-5324",
            "MES-5332A",
        ]:
            if pwr_type == "AC":
                part_no = "PM160-220/12"
            elif pwr_type == "DC":
                part_no = "PM100-48/12"
            elif pwr_type == "N/A":
                part_no = "PM160-220/12"
            else:
                raise self.NotSupportedError("Unknown PS type: %s" % pwr_type)
        elif platform in ["MES-5148", "MES-5248", "MES-5448", "MES-7048"]:
            if pwr_type == "AC":
                part_no = "PM350-220/12"
            elif pwr_type == "DC":
                part_no = "PM350-48/12"
            elif pwr_type == "N/A":
                part_no = "PM350-220/12"
            else:
                raise self.NotSupportedError("Unknown PS type: %s" % pwr_type)
        elif platform in ["MES-2348P"]:
            part_no = "PM950"
        else:
            raise self.NotSupportedError("PS on unknown platform: %s" % platform)
        if type not in ["Main", "Redundant"]:
            raise self.NotSupportedError("Unknown PS type: %s" % type)
        return {"type": "PWR", "vendor": "ELTEX", "part_no": part_no, "number": type}

    def get_trans(self, ifname):
        if self.has_detail:
            try:
                v = self.cli("show fiber-ports optical-transceiver detailed interface %s" % ifname)
            except self.CLISyntaxError:
                self.has_detail = False
        if not self.has_detail:
            v = self.cli("show fiber-ports optical-transceiver interface %s" % ifname)
        match = self.rx_trans.search(v)
        r = {"type": "XCVR", "vendor": match.group("vendor")}
        if match.group("serial"):
            r["serial"] = match.group("serial")
        if match.group("revision"):
            r["revision"] = match.group("revision")
        if ifname.startswith("gi"):
            r["number"] = "gi%s" % ifname.split("/")[-1]
        if ifname.startswith("te"):
            r["number"] = "te%s" % ifname.split("/")[-1]
        if match.group("part_no"):
            part_no = match.group("part_no")
        else:
            r["vendor"] = "OEM"
            code = match.group("code")
            if code == "1000BASE-LX":
                part_no = "NoName | Transceiver | 1G | SFP LX"
            elif code == "BaseBX10":
                wavelength = match.group("wavelength")
                if wavelength == "1310 nm":
                    part_no = "NoName | Transceiver | 1G | SFP BX10D"
                elif wavelength == "1490 nm":
                    part_no = "NoName | Transceiver | 1G | SFP BX10U"
                else:
                    # raise self.NotSupportedError()
                    part_no = "NoName | Transceiver | 1G | SFP"
            elif code == "1000BASE-T":
                part_no = "NoName | Transceiver | 1G | SFP T"
            elif code == "10GBASE-LR":
                part_no = "NoName | Transceiver | 10G | SFP+ LR"
            elif code == "10GBASE-ER":
                part_no = "NoName | Transceiver | 10G | SFP+ ER"
            elif code == "unknown":
                part_no = "NoName | Transceiver | 1G | SFP"
            else:
                raise self.NotSupportedError("Unknown Compliance code: %s" % code)
        r["part_no"] = part_no
        return r

    def get_optical_ports(self):
        opt_ports = []
        try:
            v = self.cli("show fiber-ports optical-transceiver")
            for i in parse_table(v, footer=r"Temp\s+- Internally measured transceiver temperature"):
                if i[1] in ["OK", "N/S"] or is_int(i[1]):
                    opt_ports += [i[0]]
        except self.CLISyntaxError:
            pass
        return opt_ports

    def execute_cli(self, **kwargs):
        res = []

        ports = self.get_optical_ports()

        if self.has_capability("Stack | Members"):
            has_unit_command = True
            for unit in self.capabilities["Stack | Member Ids"].split(" | "):
                try:
                    plat = self.cli("show system unit %s" % unit, cached=True)
                except self.CLISyntaxError:
                    # Found on MES1124M SW version 1.1.46
                    # Left for compatibility with other models
                    if unit == "1":
                        plat = self.cli("show system", cached=True)
                        has_unit_command = False
                    else:
                        raise self.NotSupportedError()
                if not self.is_has_image:
                    if has_unit_command:
                        ver = self.cli(f"show version unit {unit}", cached=True)
                    else:
                        ver = self.cli("show version", cached=True)
                else:
                    ver = ""
                if has_unit_command:
                    ser = self.cli(f"show system id unit {unit}", cached=True)
                else:
                    ser = self.cli("show system", cached=True)
                r = self.get_chassis(plat, ver, ser, unit=unit)
                platform = r["part_no"][0]
                res += [r]
                for match in self.rx_pwr.finditer(plat):
                    res += [self.get_pwr(match.group("type"), match.group("pwr_type"), platform)]
                for p in ports:
                    if p.startswith("gi") or p.startswith("te"):
                        if unit == p[2]:
                            res += [self.get_trans(p)]
        else:
            plat = self.cli("show system", cached=True)
            ver = self.cli("show version", cached=True)
            ser = self.cli("show system id", cached=True)
            r = self.get_chassis(plat, ver, ser)
            platform = r["part_no"][0]
            res = [r]
            for match in self.rx_pwr.finditer(plat):
                res += [self.get_pwr(match.group("type"), match.group("pwr_type"), platform)]
            for p in ports:
                res += [self.get_trans(p)]

        return res

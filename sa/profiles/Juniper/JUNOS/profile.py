# ---------------------------------------------------------------------
# Juniper.JUNOS profile
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re
from typing import Optional

# NOC modules
from noc.core.profile.base import BaseProfile


class Profile(BaseProfile):
    name = "Juniper.JUNOS"
    # Ignore this line: 'Last login: Tue Sep 18 09:17:21 2018 from 10.10.0.1'
    pattern_username = rb"((?!Last)\S+ login|[Ll]ogin): (?!Sun|Mon|Tue|Wed|Thu|Fri|Sat)"
    pattern_prompt = (
        rb"^(({master(?::\d+)}\n)?\S+>)|(({master(?::\d+)})?"
        rb"\[edit.*?\]\n\S+#)|(\[Type \^D at a new line to end input\])"
    )
    pattern_more = [(rb"^---\(more.*?\)---", b" "), (rb"\? \[yes,no\] .*?", b"y\n")]
    pattern_syntax_error = rb"\'\S+\' is ambiguous\.|syntax error, expecting|unknown command\."
    pattern_operation_error = rb"error: abnormal communication termination with"
    command_disable_pager = "set cli screen-length 0"
    command_enter_config = "configure"
    command_leave_config = "commit and-quit"
    command_exit = "exit"
    config_tokenizer = "curly"
    config_tokenizer_settings = {
        "line_comment": "#",
        "inline_comment": "##",
        "explicit_eol": ";",
        "start_of_group": "[",
        "end_of_group": "]",
        # "string_quote": "\""
    }
    config_normalizer = "JunOSNormalizer"
    confdb_defaults = [
        ("hints", "interfaces", "defaults", "admin-status", True),
        ("hints", "protocols", "ntp", "mode", "server"),
        ("hints", "protocols", "ntp", "version", "3"),
    ]
    config_applicators = ["IfaceTypeJunosApplicator"]

    collators = ["noc.core.confdb.collator.ifpath.IfPathCollator"]

    matchers = {
        "is_has_lldp": {"platform": {"$regex": "ex|mx|qfx|acx|srx"}},
        "is_switch": {"platform": {"$regex": "ex|qfx"}},
        "is_olive": {"platform": {"$regex": "olive"}},
        "is_work_em": {"platform": {"$regex": "vrr|csrx"}},
        "is_gte_16": {"version": {"$gte": "16"}},
        "is_srx_6xx": {"platform": {"$regex": r"srx6.\d+"}},
        "is_cli_help_supported": {"caps": {"$in": ["Juniper | CLI | Help"]}},
    }

    rx_ver = re.compile(r"\d+")

    # https://www.juniper.net/documentation/en_US/junos/topics/reference/general/junos-release-numbers.html
    def cmp_version(self, x, y):
        """
        Compare versions.

        Version format:
        <major>.<minor>R<h>.<l>
        """
        # FRS/maintenance release software
        if "R" in x and "R" in y:
            pass
        # Feature velocity release software
        elif "F" in x and "F" in y:
            pass
        # Beta release software
        elif "B" in x and "B" in y:
            pass
        # Internal release software:
        # private software release for verifying fixes
        elif "I" in x and "I" in y:
            pass
        # Service release software:
        # released to customers to solve a specific problem—this release
        # will be maintained along with the life span of the underlying release
        elif "S" in x and "S" in y:
            pass
        # Special (eXception) release software:
        # releases that follow a numbering system that differs from
        # the standard Junos OS release numbering
        elif "X" in x and "X" in y:
            pass
        # https://kb.juniper.net/InfoCenter/index?page=content&id=KB30092
        else:
            return None

        a = [int(z) for z in self.rx_ver.findall(x)]
        b = [int(z) for z in self.rx_ver.findall(y)]
        return (a > b) - (a < b)

    def generate_prefix_list(self, name, pl):
        """
        prefix-list generator. _pl_ is a list of (prefix, min_len, max_len)
        """
        rf = []
        for prefix, min_len, max_len in pl:
            if min_len == max_len:
                rf += ["    route-filter %s exact;" % prefix]
            else:
                rf += ["    route-filter %s upto /%d" % (prefix, max_len)]
        r = ["term pass {", "    from {"]
        r += rf
        r += ["    }", "    then next policy;", "}", "term reject {", "    then reject;", "}"]
        return "\n".join(r)

    def get_interface_names(self, name):
        """
        TODO: for QFX convert it from ifIndex
        QFX send like:
        Port type          : Locally assigned
        Port ID            : 546
        """
        names = []
        n = self.convert_interface_name(name)
        if n.endswith(".0"):
            names += [n[:-2]]
        return names

    internal_interfaces = re.compile(
        r"^(lc-|cbp|demux|dsc|gre|ipip|lsi|mtun|pimd|pime|pp|tap|pip|sp-|"
        r"em|jsrv|pfe|pfh|vcp|mt-|pd|pe|vt-|vtep|ms-|pc-|sp-|fab|mams-|"
        r"bme|esi|ams|rbeb|fti)"
    )
    internal_interfaces_without_em = re.compile(
        r"^(lc-|cbp|demux|dsc|gre|ipip|lsi|mtun|pimd|pime|pp|tap|pip|sp-|"
        r"jsrv|pfe|pfh|vcp|mt-|pd|pe|vt-|vtep|ms-|pc-|sp-|fab|mams-|"
        r"bme|esi|ams|rbeb|fti)"
    )
    internal_interfaces_olive = re.compile(
        r"^(lc-|cbp|demux|dsc|gre|ipip|lsi|mtun|pimd|pime|pp|tap|pip|sp-)"
    )

    def valid_interface_name(self, script, name):
        if script.is_olive:
            internal = self.internal_interfaces_olive
        else:
            if script.is_work_em:
                # em - is a working interface
                internal = self.internal_interfaces_without_em
            else:
                internal = self.internal_interfaces
        # Skip internal interfaces
        if internal.search(name):
            return False
        if "." in name:
            try:
                ifname, unit = name.split(".")
            except ValueError:
                return True
            # See `logical-interface-unit-range`
            if int(unit) > 16385:
                return False
        return True

    def command_exist(self, script, cmd) -> Optional[bool]:
        if not script.is_cli_help_supported:
            return None
        c = script.cli(
            f'help apropos "{cmd}" | match "^show {cmd}" ', cached=True, ignore_errors=True
        )
        return ("show " + cmd in c) and ("error: nothing matches" not in c)

    @classmethod
    def get_interface_type(cls, name):
        if name.startswith("lo"):
            return "loopback"
        elif name.startswith(("fxp", "me")):
            return "management"
        elif name.startswith(("ae", "reth", "fab", "swfab")):
            return "aggregated"
        elif name.startswith(("vlan", "vme")):
            return "SVI"
        elif name.startswith("irb"):
            return "SVI"
        elif name.startswith(("fc", "fe", "ge", "xe", "sxe", "xle", "et", "fte")):
            return "physical"
        elif name.startswith(("gr", "ip", "st")):
            return "tunnel"
        elif name.startswith("em"):
            return "management"
        else:
            return "unknown"

# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Pretty command ver.12
# ----------------------------------------------------------------------
# Copyright (C) 2007-2021 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import argparse
import asyncio
import datetime
from io import BytesIO

# Third-party modules
import xlsxwriter
import logging

# NOC modules
from noc.core.management.base import BaseCommand
from noc.core.validators import is_ipv4
from noc.core.ioloop.ping import Ping
from noc.core.ip import IP
from noc.core.ioloop.snmp import snmp_get, SNMPError
from noc.core.mib import mib
from noc.core.snmp.version import SNMP_v1, SNMP_v2c
from noc.sa.models.managedobject import ManagedObject, ManagedObjectProfile
from noc.sa.models.authprofile import AuthProfile
from noc.sa.models.managedobject import AdministrativeDomain
from noc.inv.models.networksegment import NetworkSegment
from noc.main.models.pool import Pool
from noc.sa.models.profile import Profile
from noc.inv.models.platform import Platform
from noc.services.mailsender.service import MailSenderService
from noc.core.comp import smart_text
from noc.core.mongo.connection import connect


# example
# ./noc network-scan 10.0.0.0/24
# ./noc network-scan --autoadd test --email example@example.org --format xlsx 10.0.0.0/24
# ./noc network-scan --in /opt/net/nets --exclude /opt/net/exclude


class Command(BaseCommand):
    DEFAULT_OID = "1.3.6.1.2.1.1.2.0"
    DEFAULT_COMMUNITY = "public"
    CHECK_OIDS = [mib["SNMPv2-MIB::sysObjectID.0"], mib["SNMPv2-MIB::sysName.0"]]
    CHECK_VERSION = {SNMP_v1: "snmp_v2c_get", SNMP_v2c: "snmp_v1_get"}
    SNMP_VERSION = {0: "SNMP_v1", 1: "SNMP_v2c"}

    def add_arguments(self, parser):
        parser.add_argument("--in", action="append", dest="input", help="File with addresses")
        parser.add_argument(
            "--import", action="append", dest="imports", help="File to import into NOC"
        )
        parser.add_argument(
            "--exclude", action="append", dest="exclude", help="File with addresses for exclusion"
        )
        parser.add_argument(
            "--jobs", action="store", type=int, default=100, dest="jobs", help="Concurrent jobs"
        )
        parser.add_argument("addresses", nargs=argparse.REMAINDER, help="Object name")
        parser.add_argument("--community", action="append", help="SNMP community")
        parser.add_argument("--oid", default=self.CHECK_OIDS, action="append", help="SNMP GET OIDs")
        parser.add_argument("--timeout", type=int, default=1, help="SNMP GET timeout")
        parser.add_argument("--convert", type=bool, default=False, help="convert mac address")
        parser.add_argument("--version", type=int, help="version snmp check")
        parser.add_argument("--auth", help="auth profile")
        parser.add_argument("--pool", help="name pool", default="default")
        parser.add_argument("--autoadd", help="add object", default="")
        parser.add_argument("--mail", help="mail notification_group name")
        parser.add_argument("--email", action="append", help="mailbox list")
        parser.add_argument("--format", default="csv", help="Format file (csv or xlsx)")

    def handle(
        self,
        input,
        imports,
        exclude,
        addresses,
        jobs,
        community,
        oid,
        timeout,
        convert,
        version,
        auth,
        pool,
        autoadd,
        mail,
        email,
        format,
        *args,
        **options,
    ):
        async def ping_task():
            queue = asyncio.Queue(maxsize=self.jobs)
            for _ in range(self.jobs):
                asyncio.create_task(self.ping_worker(queue))
            # Read exclude addresses from files
            """
            file format example
            10.0.0.1
            10.1.1.0/24
            10.1.2.1
            """
            if exclude:
                for fn in exclude:
                    try:
                        with open(fn) as f:
                            for line in f:
                                line = line.strip()
                                ip = line.split("/")
                                if is_ipv4(ip[0]):
                                    if len(ip) == 2:
                                        ip = IP.prefix(line)
                                        first = ip.first
                                        last = ip.last
                                        for x in first.iter_address(until=last):
                                            ip2 = str(x).split("/")
                                            self.hosts_exclude.add(ip2[0])
                                    else:
                                        self.hosts_exclude.add(line)
                    except OSError as e:
                        self.die("Cannot read file %s: %s\n" % (fn, e))
            # Direct addresses 10.0.0.1 or 10.0.0.0/24
            for a in addresses:
                self.addresses = set()
                self.nets.append(a)
                ip = a.split("/")
                if is_ipv4(ip[0]):
                    if len(ip) == 2:
                        ip = IP.prefix(a)
                        first = ip.first
                        last = ip.last
                        for x in first.iter_address(until=last):
                            ip2 = str(x).split("/")
                            if ip2[0] not in self.hosts_exclude:
                                await queue.put(ip2[0])
                    else:
                        if a not in self.hosts_exclude:
                            await queue.put(a)

            # Read addresses from files
            """
            file format example
            10.0.0.1
            10.1.1.0/24
            10.1.2.1
            """
            if input:
                for fn in input:
                    try:
                        with open(fn) as f:
                            for line in f:
                                line = line.strip()
                                ip = line.split("/")
                                if is_ipv4(ip[0]):
                                    self.nets.append(line)
                                    if len(ip) == 2:
                                        ip = IP.prefix(line)
                                        first = ip.first
                                        last = ip.last
                                        for x in first.iter_address(until=last):
                                            ip2 = str(x).split("/")
                                            if ip2[0] not in self.hosts_exclude:
                                                await queue.put(ip2[0])
                                    else:
                                        if line not in self.hosts_exclude:
                                            await queue.put(line)

                    except OSError as e:
                        self.die("Cannot read file %s: %s\n" % (fn, e))
            await queue.join()

        async def snmp_task():
            queue = asyncio.Queue(maxsize=self.jobs)
            for _ in range(self.jobs):
                asyncio.create_task(self.snmp_worker(queue, community, oid, timeout, self.version))
            for a in self.enable_ping:
                await queue.put(a)
            await queue.join()

        connect()
        self.addresses = set()  # ip for ping
        self.enable_ping = set()  # ip ping
        self.not_ping = set()  # ip not ping
        self.enable_snmp = set()  # ip responding snmp
        self.hosts_enable = set()  # ip in noc
        self.hosts_exclude = set()  # ip exclude
        self.mo = {}
        self.snmp = {}
        self.nets = []  # nets
        self.count_ping = 0
        self.count_not_ping = 0
        self.count_snmp = 0
        self.count_net = 0

        # параметры by-default
        is_managed = "True"
        administrative_domain = "default"
        profile = "Generic.Host"
        # object_profile = "default"
        description = "create object %s" % (datetime.datetime.now().strftime("%Y%m%d"))
        segment = "ALL"
        # auth_profile="autoadd"
        # scheme = "1"
        # address = ""
        # port = ""
        # user=""
        # password=""
        # super_password = ""
        # remote_path = ""
        # trap_source_ip = ""
        # trap_community = ""
        # snmp_ro=""
        # snmp_rw=""
        # vc_domain = "default"
        # vrf = ""
        # termination_group = ""
        # service_terminator = ""
        # shape = "Cisco/router"
        # config_filter_rule = ""
        # config_diff_filter_rule = ""
        # config_validation_rule = ""
        # max_scripts = "1"
        labels = ["autoadd"]
        # pool = "default"
        # container = ""
        # trap_source_type = "d"
        # syslog_source_type = "d"
        # object_profile="default"
        # time_pattern = ""
        # x = ""
        # y = ""
        # default_zoom = ""

        if version is None:
            self.version = [1, 0]
        else:
            self.version = [version]
        try:
            self.pool = Pool.objects.get(name=pool)
        except Pool.DoesNotExist:
            self.die("Invalid pool-%s" % (pool))
        # snmp community
        if not community:
            community = []
            if auth:
                try:
                    self.auth = AuthProfile.objects.get(name=auth)
                    if self.auth.enable_suggest:
                        for ro, rw in self.auth.iter_snmp():
                            community.append(ro)
                except AuthProfile.DoesNotExist:
                    self.die("Invalid authprofile-%s" % (auth))
            elif pool:
                auth = f"TG.{pool}"
                try:
                    self.auth = AuthProfile.objects.get(name=auth)
                    if self.auth.enable_suggest:
                        for ro, rw in self.auth.iter_snmp():
                            community.append(ro)
                except AuthProfile.DoesNotExist:
                    self.die("Invalid authprofile-%s" % (auth))
            else:
                community = [self.DEFAULT_COMMUNITY]

        # auto add objects profile
        if autoadd:
            try:
                self.object_profile = ManagedObjectProfile.objects.get(name=autoadd)
            except ManagedObjectProfile.DoesNotExist:
                self.die("Invalid object profile-%s" % (autoadd))

        # создание списка наличия мо в noc
        moall = ManagedObject.objects.filter(is_managed=True)
        if pool:
            moall = moall.filter(pool=self.pool)
        for mm in moall:
            self.hosts_enable.add(mm.address)
            self.mo[mm.address] = {
                "name": mm.name,
                "labels": mm.labels,
                "is_managed": mm.is_managed,
                "snmp_ro": mm.auth_profile.snmp_ro if mm.auth_profile else mm.snmp_ro,
            }
        # добавить в список мо с remote:deleted
        moall = ManagedObject.objects.filter(is_managed=False).exclude(
            labels__contains=["remote:deleted"]
        )
        if pool:
            moall = moall.filter(pool=self.pool)
        for mm in moall:
            if mm.address not in self.hosts_enable:
                self.hosts_enable.add(mm.address)
                self.mo[mm.address] = {
                    "name": mm.name,
                    "labels": mm.labels,
                    "is_managed": mm.is_managed,
                    "snmp_ro": mm.auth_profile.snmp_ro if mm.auth_profile else mm.snmp_ro,
                }
        # Ping
        self.ping = Ping()
        self.jobs = jobs
        asyncio.run(ping_task())
        print("ver.12")
        print("enable_ping ", len(self.enable_ping))
        # snmp
        asyncio.run(snmp_task())
        print("enable_snmp ", len(self.enable_snmp))

        data = "IP;Доступен по ICMP;IP есть;is_managed;SMNP sysname;SNMP sysObjectId;Vendor;Model;Имя;pool;labels\n"
        # столбцы x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12
        for ipx in self.enable_ping:
            x2 = "Да"
            x4 = x5 = x6 = x7 = x8 = x9 = x11 = "Не определено"
            if ipx in self.hosts_enable:
                x3 = "Да"
                x8 = self.mo[ipx]["name"]
                x11 = str(self.mo[ipx]["is_managed"])
                if self.mo[ipx]["labels"]:
                    x9 = ",".join(self.mo[ipx]["labels"] if self.mo[ipx]["labels"] else [])
            else:
                if autoadd:
                    m = ManagedObject(
                        name=ipx,
                        is_managed=is_managed,
                        auth_profile=self.auth,
                        administrative_domain=AdministrativeDomain.objects.get(
                            name=administrative_domain
                        ),
                        profile=Profile.objects.get(name=profile),
                        description=description,
                        object_profile=self.object_profile,
                        segment=NetworkSegment.objects.get(name=segment),
                        scheme=1,
                        address=ipx,
                        labels=labels,
                        pool=Pool.objects.get(name=pool),
                    )
                    m.save()
                x3 = "Нет"
            if ipx in self.enable_snmp:
                # ['1.3.6.1.2.1.1.2.0', '1.3.6.1.2.1.1.5.0']
                if "1.3.6.1.2.1.1.2.0" in self.snmp[ipx]:
                    x5 = self.snmp[ipx]["1.3.6.1.2.1.1.2.0"]
                    for p in Platform.objects.filter(snmp_sysobjectid=x5):
                        if p:
                            x6 = p.vendor
                            x7 = p.name
                else:
                    x5 = "Не определено"

                if "1.3.6.1.2.1.1.5.0" in self.snmp[ipx]:
                    sysname = self.snmp[ipx]["1.3.6.1.2.1.1.5.0"]
                    x4 = sysname
                else:
                    x4 = "Не определено"
                    # try:
                    #    sysname = self.snmp[ipx]["1.3.6.1.2.1.1.5.0"]
                    #    x4 = sysname
                    # except:
                    #    x4 = "Не определено"
            s = ";".join(
                [
                    smart_text(ipx),
                    smart_text(x2),
                    smart_text(x3),
                    smart_text(x11),
                    smart_text(x4),
                    smart_text(x5),
                    smart_text(x6),
                    smart_text(x7),
                    smart_text(x8),
                    smart_text(pool),
                    smart_text(x9),
                ]
            )
            data += s + "\n"

        fn = "/tmp/report.csv"
        file = open(fn, "w")
        file.write(data)
        file.close()
        # output in csv or mail
        if email:
            bodymessage = "Отчет во вложении.\n\nОтсканированы сети:\n"
            for adr in self.nets:
                bodymessage += adr + "\n"
            filename = "found_ip_%s" % (datetime.datetime.now().strftime("%Y%m%d"))
            if format == "csv":
                f = "%s.csv" % filename
                attach = [{"filename": f, "data": data}]
            elif format == "xlsx":
                f = "%s.xlsx" % filename
                response = BytesIO()
                wb = xlsxwriter.Workbook(response)
                ws = wb.add_worksheet("Objects")
                row = 0
                ss = data.split("\n")
                for line in ss:
                    row_data = str(line).strip("\n")
                    rr = row_data.split(";")
                    ws.write_row(row, 0, tuple(rr))

                    # Move on to the next worksheet row.
                    row += 1
                wb.close()
                response.seek(0)
                attach = [
                    {"filename": f, "data": response.getvalue(), "transfer-encoding": "base64"}
                ]
                response.close()
            ms = MailSenderService()
            ms.logger = logging.getLogger("network_scan")
            msg = {
                "address": email,
                "subject": "Отчет о расхождениях (%s)" % pool,
                "body": bodymessage,
                "attachments": attach,
            }
            ms.send_mail("11", msg)
        else:
            print(data)

    async def ping_worker(self, queue):
        while True:
            a = await queue.get()
            if a:
                rtt = await self.ping.ping_check(a, count=3, timeout=500)
                if rtt:
                    self.enable_ping.add(a)
            queue.task_done()
            if not a:
                break

    async def snmp_worker(self, queue, community, oid, timeout, version):
        while True:
            a = await queue.get()
            if a:
                if a in self.hosts_enable:
                    community = [self.mo[a]["snmp_ro"]]
                if not community[0] is None:
                    for c in community:
                        for ver in version:
                            try:
                                self.r = await snmp_get(
                                    address=a,
                                    oids=dict((k, k) for k in oid),
                                    community=c,
                                    version=ver,
                                    timeout=timeout,
                                )
                                # self.s = "OK"
                                self.enable_snmp.add(a)
                                self.snmp[a] = self.r
                                self.snmp[a]["version"] = ver
                                self.snmp[a]["community"] = c
                                break
                            except SNMPError as e:
                                # self.s = "FAIL"
                                self.r = str(e)
                            except Exception as e:
                                # self.s = "EXCEPTION"
                                self.r = str(e)
                                break
            queue.task_done()
            if not a:
                break


if __name__ == "__main__":
    Command().run()

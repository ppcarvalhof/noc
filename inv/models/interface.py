# ---------------------------------------------------------------------
# Interface model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import datetime
import logging

# Third-party modules
from mongoengine.document import Document
from mongoengine.fields import (
    StringField,
    IntField,
    BooleanField,
    ListField,
    DateTimeField,
    ReferenceField,
    ObjectIdField,
    DictField,
)
from pymongo import ReadPreference
from typing import Optional, Iterable, List

# NOC Modules
from noc.config import config
from noc.core.mongo.fields import ForeignKeyField, PlainReferenceField
from noc.core.resourcegroup.decorator import resourcegroup
from noc.core.mx import send_message, MX_LABELS, MX_H_VALUE_SPLITTER
from noc.sa.models.managedobject import ManagedObject
from noc.sa.interfaces.base import MACAddressParameter
from noc.sa.interfaces.igetinterfaces import IGetInterfaces
from noc.main.models.label import Label
from noc.project.models.project import Project
from noc.sa.models.service import Service
from noc.core.model.decorator import on_delete, on_delete_check
from noc.core.change.decorator import change
from noc.core.comp import DEFAULT_ENCODING
from noc.core.wf.decorator import workflow
from noc.wf.models.state import State
from .interfaceprofile import InterfaceProfile
from .coverage import Coverage


INTERFACE_TYPES = IGetInterfaces.returns.element.attrs["interfaces"].element.attrs["type"].choices
INTERFACE_PROTOCOLS = (
    IGetInterfaces.returns.element.attrs["interfaces"]
    .element.attrs["enabled_protocols"]
    .element.choices
)


logger = logging.getLogger(__name__)


# @Label.dynamic_classification(profile_model_id="inv.InterfaceProfile")
@on_delete
@change
@resourcegroup
@Label.model
@workflow
@on_delete_check(
    clean=[
        ("inv.Interface", "aggregated_interface"),
    ],
    ignore=[
        ("inv.Link", "interfaces"),
        ("inv.SubInterface", "interface"),
        ("inv.MACDB", "interface"),
    ],
)
class Interface(Document):
    """
    Interfaces
    """

    meta = {
        "collection": "noc.interfaces",
        "strict": False,
        "auto_create_index": False,
        "indexes": [
            ("managed_object", "name"),
            "mac",
            ("managed_object", "ifindex"),
            "service",
            "aggregated_interface",
            "labels",
            "profile",
            "state",
            "effective_labels",
        ],
    }
    managed_object: "ManagedObject" = ForeignKeyField(ManagedObject)
    name = StringField()  # Normalized via Profile.convert_interface_name
    # Optional default interface name in case the `name` can be reconfigured
    default_name = StringField()
    type = StringField(choices=[(x, x) for x in INTERFACE_TYPES])
    description = StringField(required=False)
    ifindex = IntField(required=False)
    mac = StringField(required=False)
    aggregated_interface = PlainReferenceField("self", required=False)
    enabled_protocols = ListField(
        StringField(choices=[(x, x) for x in INTERFACE_PROTOCOLS]), default=[]
    )
    profile: "InterfaceProfile" = PlainReferenceField(
        InterfaceProfile, default=InterfaceProfile.get_default_profile
    )
    # profile locked on manual user change
    profile_locked = BooleanField(required=False, default=False)
    #
    project = ForeignKeyField(Project)
    state = PlainReferenceField(State)
    # Current status
    admin_status = BooleanField(required=False)
    oper_status = BooleanField(required=False)
    oper_status_change = DateTimeField(required=False, default=datetime.datetime.now)
    full_duplex = BooleanField(required=False)
    in_speed = IntField(required=False)  # Input speed, kbit/s
    out_speed = IntField(required=False)  # Output speed, kbit/s
    bandwidth = IntField(required=False)  # Configured bandwidth, kbit/s
    # Interface hints: uplink, uni, nni
    hints = ListField(StringField(required=False))
    # Coverage
    coverage = PlainReferenceField(Coverage)
    technologies = ListField(StringField())
    # External NRI interface name
    nri_name = StringField()
    #
    service = ReferenceField(Service)
    # Resource groups
    static_service_groups = ListField(ObjectIdField())
    effective_service_groups = ListField(ObjectIdField())
    static_client_groups = ListField(ObjectIdField())
    effective_client_groups = ListField(ObjectIdField())
    # Labels
    labels = ListField(StringField())
    effective_labels = ListField(StringField())
    extra_labels = DictField()

    PROFILE_LINK = "profile"

    def __str__(self):
        return "%s: %s" % (self.managed_object.name, self.name)

    @classmethod
    def get_by_id(cls, id) -> Optional["Interface"]:
        return Interface.objects.filter(id=id).first()

    def clean(self):
        if self.extra_labels:
            self.labels += [
                ll
                for ll in Label.merge_labels(self.extra_labels.values())
                if Interface.can_set_label(ll)
            ]

    @classmethod
    def get_component(
        cls, managed_object: "ManagedObject", interface=None, ifindex=None, **kwargs
    ) -> Optional["Interface"]:
        from noc.inv.models.subinterface import SubInterface

        q = {}
        if interface:
            q["name"] = managed_object.get_profile().convert_interface_name(interface)
        elif ifindex:
            q["ifindex"] = int(ifindex)
        if not q:
            return
        q["managed_object"] = managed_object.id
        iface = Interface.objects.filter(**q).first()
        if iface:
            return iface
        # Try to find subinterface
        si = SubInterface.objects.filter(**q).first()
        if si:
            return si.interface

    def iter_changed_datastream(self, changed_fields=None):
        if config.datastream.enable_managedobject:
            yield "managedobject", self.managed_object.id
        yield "cfgmetricsources", f"sa.ManagedObject::{self.managed_object.bi_id}"

    def save(self, *args, **kwargs):
        if not hasattr(self, "_changed_fields") or "name" in self._changed_fields:
            self.name = self.managed_object.get_profile().convert_interface_name(self.name)
        if (not hasattr(self, "_changed_fields") or "mac" in self._changed_fields) and self.mac:
            self.mac = MACAddressParameter().clean(self.mac)
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            raise ValueError(f"{e.__doc__}: {str(e)}")
        if not hasattr(self, "_changed_fields") or "service" in self._changed_fields:
            ServiceSummary.refresh_object(self.managed_object)

    def on_delete(self):
        from .macdb import MACDB
        from noc.fm.models.activealarm import ActiveAlarm

        # Remove all subinterfaces
        for si in self.subinterface_set.all():
            si.delete()
        # Unlink
        link = self.link
        if link:
            self.unlink()
        # Flush MACDB
        MACDB.objects.filter(interface=self.id).delete()

        # Clear Alarm
        for aa in ActiveAlarm.objects.filter(
            managed_object=self.managed_object, vars__interface=self.name
        ):
            aa.clear_alarm("Delete Interface")

    @property
    def link(self):
        """
        Return Link instance or None
        :return:
        """
        if self.type == "aggregated":
            q = {"interfaces__in": [self.id] + [i.id for i in self.lag_members]}
        else:
            q = {"interfaces": self.id}
        return Link.objects.filter(**q).first()

    @property
    def is_linked(self):
        """
        Check interface is linked
        :returns: True if interface is linked, False otherwise
        """
        if self.type == "aggregated":
            # Speedup query for labels because self.lag_members very slow
            return bool(
                next(
                    Interface._get_collection()
                    .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
                    .aggregate(
                        [
                            {
                                "$match": {
                                    "$or": [{"_id": self.id}, {"aggregated_interface": self.id}]
                                }
                            },
                            {
                                "$lookup": {
                                    "from": "noc.links",
                                    "localField": "_id",
                                    "foreignField": "interfaces",
                                    "as": "links",
                                }
                            },
                            {"$match": {"links": {"$ne": []}}},
                            {"$limit": 1},
                        ]
                    ),
                    None,
                )
            )

        else:
            return bool(
                Link._get_collection()
                .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
                .find_one({"interfaces": self.id})
            )

    def unlink(self):
        """
        Remove existing link.
        Raise ValueError if interface is not linked
        """
        link = self.link
        if link is None:
            raise ValueError("Interface is not linked")
        if link.is_ptp or link.is_lag:
            link.delete()
        elif len(link.interfaces) == 2:
            # Depleted cloud
            link.delete()
        else:
            link.interfaces = [i for i in link.interfaces if i.id != self.id]
            link.save()

    def link_ptp(self, other, method=""):
        """
        Create p-t-p link with other interface
        Raise ValueError if either of interface already connected.
        :param other: Other Iface for link
        :param method: Linking method
        :type other: Interface
        :returns: Link instance
        """

        def link_mismatched_lag(agg, phy):
            """
            Try to link LAG to physical interface
            :param agg:
            :param phy:
            :return:
            """
            l_members = [i for i in agg.lag_members if i.oper_status]
            if len(l_members) > 1:
                raise ValueError("More then one active interface in LAG")
            link = Link(interfaces=l_members + [phy], discovery_method=method)
            link.save()
            return link

        # Try to check existing LAG
        el = Link.objects.filter(interfaces=self.id).first()
        if el and other not in el.interfaces:
            el = None
        if (self.is_linked or other.is_linked) and not el:
            raise ValueError("Already linked")
        if self.id == other.id:
            raise ValueError("Cannot link with self")
        if self.type in ("physical", "management"):
            if other.type in ("physical", "management"):
                # Refine LAG
                if el:
                    left_ifaces = [i for i in el.interfaces if i not in (self, other)]
                    if left_ifaces:
                        el.interfaces = left_ifaces
                        el.save()
                    else:
                        el.delete()
                #
                link = Link(interfaces=[self, other], discovery_method=method)
                link.save()
                return link
            elif other.type == "aggregated" and other.profile.allow_lag_mismatch:
                return link_mismatched_lag(other, self)
            else:
                raise ValueError("Cannot connect %s interface to %s" % (self.type, other.type))
        elif self.type == "aggregated":
            # LAG
            if other.type == "aggregated":
                # Check LAG size match
                # Skip already linked members
                l_members = [i for i in self.lag_members if not i.is_linked]
                r_members = [i for i in other.lag_members if not i.is_linked]
                if len(l_members) != len(r_members):
                    raise ValueError("LAG size mismatch")
                # Create link
                if l_members:
                    link = Link(interfaces=l_members + r_members, discovery_method=method)
                    link.save()
                    return link
                else:
                    return
            elif self.profile.allow_lag_mismatch:
                return link_mismatched_lag(self, other)
            else:
                raise ValueError("Cannot connect %s interface to %s" % (self.type, other.type))
        raise ValueError("Cannot link")

    @classmethod
    def get_interface(cls, s):
        """
        Parse <managed object>@<interface> string
        and return interface instance or None
        """
        if "@" not in s:
            raise ValueError("Invalid interface: %s" % s)
        o, i = s.rsplit("@", 1)
        # Get managed object
        try:
            mo = ManagedObject.objects.get(name=o)
        except ManagedObject.DoesNotExist:
            raise ValueError("Invalid manged object: %s" % o)
        # Normalize interface name
        i = mo.get_profile().convert_interface_name(i)
        # Look for interface
        iface = Interface.objects.filter(managed_object=mo.id, name=i).first()
        return iface

    @property
    def subinterface_set(self):
        from .subinterface import SubInterface

        return SubInterface.objects.filter(interface=self.id)

    @property
    def lag_members(self):
        if self.type != "aggregated":
            raise ValueError("Cannot net LAG members for not-aggregated interface")
        return Interface.objects.filter(aggregated_interface=self.id)

    @property
    def status(self):
        """
        Returns interface status in form of
        Up/100/Full
        """

        def humanize_speed(speed):
            if not speed:
                return "-"
            for t, n in [(1000000, "G"), (1000, "M"), (1, "k")]:
                if speed >= t:
                    if speed // t * t == speed:
                        return "%d%s" % (speed // t, n)
                    else:
                        return "%.2f%s" % (float(speed) / t, n)
            return str(speed)

        s = [{True: "Up", False: "Down", None: "-"}[self.oper_status]]
        # Speed
        if self.oper_status:
            if self.in_speed and self.in_speed == self.out_speed:
                s += [humanize_speed(self.in_speed)]
            else:
                s += [humanize_speed(self.in_speed), humanize_speed(self.out_speed)]
            s += [{True: "Full", False: "Half", None: "-"}[self.full_duplex]]
        else:
            s += ["-", "-"]
        return "/".join(s)

    def set_oper_status(self, status):
        """
        Set current oper status
        """
        if self.oper_status == status:
            return
        now = datetime.datetime.now()
        if self.oper_status != status and (
            not self.oper_status_change or self.oper_status_change < now
        ):
            self.update(oper_status=status, oper_status_change=now)
            if self.profile.is_enabled_notification:
                logger.debug("Sending status change notification")
                send_message(
                    data={
                        "name": self.name,
                        "description": self.description,
                        "is_uni": self.profile.is_uni,
                        "profile": {"id": str(self.profile.id), "name": self.profile.name},
                        "status": status,
                        "full_duplex": self.full_duplex,
                        "managed_object": self.managed_object.get_message_context(),
                    },
                    message_type="interface_status_change",
                    headers={
                        MX_LABELS: MX_H_VALUE_SPLITTER.join(self.effective_labels).encode(
                            encoding=DEFAULT_ENCODING
                        ),
                    },
                )

    @property
    def parent(self) -> "Interface":
        """
        Returns aggregated interface for LAG or
        self for non-aggregated interface
        """
        if self.aggregated_interface:
            return self.aggregated_interface
        else:
            return self

    def get_profile(self) -> InterfaceProfile:
        if self.profile:
            return self.profile
        return InterfaceProfile.get_default_profile()

    @classmethod
    def can_set_label(cls, label):
        return Label.get_effective_setting(label, setting="enable_interface")

    @classmethod
    def iter_effective_labels(cls, instance: "Interface") -> Iterable[List[str]]:
        from noc.inv.models.subinterface import SubInterface

        yield list(instance.labels or [])
        # if instance.hints:
        #     # Migrate to labels
        #     yield Label.ensure_labels(instance.hints, enable_interface=True)
        if instance.profile.labels:
            yield list(instance.profile.labels)
        yield list(InterfaceProfile.iter_lazy_labels(instance.profile))
        yield Label.get_effective_regex_labels("interface_name", instance.name)
        yield Label.get_effective_regex_labels("interface_description", instance.description or "")
        if instance.managed_object:
            yield [
                ll
                for ll in instance.managed_object.get_effective_labels()
                if ll != "noc::is_linked::="
            ]
        if instance.service:
            yield from Service.iter_effective_labels(instance.service)
        if instance.parent.id and instance.type == "physical" and instance.is_linked:
            # Idle Discovery When create Aggregate interface (fixed not use lag_members)
            yield ["noc::is_linked::="]
        if instance.parent.id:
            # When create id is None
            # Do not use SECONDARY_PREFERRED, when update labels right after
            # create or update SubInterface changes not keep up on Secondary
            for el in SubInterface.objects.filter(
                enabled_afi__in=["BRIDGE", "IPv4"], interface=instance.parent.id
            ).scalar("effective_labels"):
                yield el


# Avoid circular references
from noc.sa.models.servicesummary import ServiceSummary
from .link import Link

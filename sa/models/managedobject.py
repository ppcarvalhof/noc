# ----------------------------------------------------------------------
# ManagedObject
# ----------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
import difflib
from collections import namedtuple
import logging
import os
import re
import operator
from threading import Lock
import datetime
import warnings
from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Iterable, List, Any, Dict, Set, Optional

# Third-party modules
import orjson
import cachetools
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    Q,
    CharField,
    BooleanField,
    ForeignKey,
    IntegerField,
    FloatField,
    DateTimeField,
    BigIntegerField,
    SET_NULL,
    CASCADE,
)
from pydantic import BaseModel
from pymongo import ReadPreference, ASCENDING

# NOC modules
from noc.core.model.base import NOCModel
from noc.config import config
from noc.core.wf.diagnostic import (
    DiagnosticState,
    DiagnosticConfig,
    DIAGNOSTIC_CHECK_STATE,
    PROFILE_DIAG,
    SNMP_DIAG,
    CLI_DIAG,
    SNMPTRAP_DIAG,
    SYSLOG_DIAG,
    HTTP_DIAG,
)
from noc.core.checkers.base import CheckData, Check
from noc.core.mx import send_message, MX_LABELS, MX_H_VALUE_SPLITTER, MX_ADMINISTRATIVE_DOMAIN_ID
from noc.core.deprecations import RemovedInNOC2301Warning
from noc.aaa.models.user import User
from noc.aaa.models.group import Group
from noc.main.models.pool import Pool
from noc.main.models.timepattern import TimePattern
from noc.main.models.remotesystem import RemoteSystem
from noc.vc.models.l2domain import L2Domain
from noc.main.models.label import Label
from noc.inv.models.networksegment import NetworkSegment
from noc.sa.models.profile import Profile
from noc.inv.models.capsitem import ModelCapsItem
from noc.inv.models.vendor import Vendor
from noc.inv.models.platform import Platform
from noc.inv.models.firmware import Firmware
from noc.inv.models.firmwarepolicy import FirmwarePolicy
from noc.project.models.project import Project
from noc.fm.models.ttsystem import TTSystem, DEFAULT_TTSYSTEM_SHARD
from noc.core.model.fields import (
    INETField,
    DocumentReferenceField,
    CachedForeignKey,
    ObjectIDArrayField,
    PydanticField,
)
from noc.core.model.sql import SQL
from noc.core.stencil import stencil_registry
from noc.core.validators import is_ipv4, is_ipv4_prefix
from noc.core.ip import IP
from noc.sa.interfaces.base import MACAddressParameter
from noc.core.gridvcs.manager import GridVCSField
from noc.main.models.textindex import full_text_search, TextIndex
from noc.core.scheduler.job import Job
from noc.main.models.handler import Handler
from noc.core.handler import get_handler
from noc.core.script.loader import loader as script_loader
from noc.core.model.decorator import (
    on_save,
    on_init,
    on_delete,
    on_delete_check,
    _get_field_snapshot,
)
from noc.inv.models.object import Object
from noc.inv.models.resourcegroup import ResourceGroup
from noc.inv.models.capability import Capability
from noc.core.defer import call_later
from noc.core.cache.decorator import cachedmethod
from noc.core.cache.base import cache
from noc.core.script.caller import SessionContext, ScriptCaller
from noc.core.bi.decorator import bi_sync
from noc.core.script.scheme import SCHEME_CHOICES
from noc.core.matcher import match
from noc.core.change.decorator import change
from noc.core.change.policy import change_tracker
from noc.core.resourcegroup.decorator import resourcegroup
from noc.core.confdb.tokenizer.loader import loader as tokenizer_loader
from noc.core.confdb.engine.base import Engine
from noc.core.comp import smart_text, DEFAULT_ENCODING
from noc.main.models.glyph import Glyph
from noc.core.topology.types import ShapeOverlayPosition, ShapeOverlayForm
from noc.core.models.problem import ProblemItem
from noc.core.models.cfgmetrics import MetricCollectorConfig, MetricItem
from .administrativedomain import AdministrativeDomain
from .authprofile import AuthProfile
from .managedobjectprofile import ManagedObjectProfile
from .objectstatus import ObjectStatus
from .objectdiagnosticconfig import ObjectDiagnosticConfig

# Increase whenever new field added or removed
MANAGEDOBJECT_CACHE_VERSION = 42
CREDENTIAL_CACHE_VERSION = 5

Credentials = namedtuple(
    "Credentials", ["user", "password", "super_password", "snmp_ro", "snmp_rw", "snmp_rate_limit"]
)


class MaintenanceItem(BaseModel):
    start: datetime.datetime
    # Time pattern when maintenance is active
    # None - active all the time
    time_pattern: Optional[int] = None
    stop: Optional[datetime.datetime] = None


class MaintenanceItems(BaseModel):
    __root__: Dict[str, MaintenanceItem]


class CapsItems(BaseModel):
    __root__: List[ModelCapsItem]


class CheckStatus(BaseModel):
    name: str
    status: bool  # True - OK, False - Fail
    arg0: Optional[str] = None
    skipped: bool = False
    error: Optional[str] = None  # Description if Fail


class DiagnosticItem(BaseModel):
    diagnostic: str
    state: DiagnosticState = DiagnosticState("unknown")
    checks: Optional[List[CheckStatus]]
    # scope: Literal["access", "all", "discovery", "default"] = "default"
    # policy: str = "ANY
    reason: Optional[str] = None
    changed: Optional[datetime.datetime] = None

    def get_check_state(self):
        # Any policy
        return any(c.status for c in self.checks if not c.skipped)


class DiagnosticItems(BaseModel):
    __root__: Dict[str, DiagnosticItem]


def default(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, datetime.datetime):
        return obj.replace(microsecond=0).isoformat(sep=" ")
    raise TypeError


@dataclass(frozen=True)
class ObjectUplinks(object):
    object_id: int
    uplinks: List[int]
    rca_neighbors: List[int]


id_lock = Lock()
e_labels_lock = Lock()

logger = logging.getLogger(__name__)


@full_text_search
@Label.dynamic_classification(
    profile_model_id="sa.ManagedObjectProfile", profile_field="object_profile"
)
@bi_sync
@on_init
@on_save
@on_delete
@change
@resourcegroup
@Label.model
@on_delete_check(
    check=[
        # ("cm.ValidationRule.ObjectItem", ""),
        ("fm.ActiveAlarm", "managed_object"),
        ("fm.ActiveEvent", "managed_object"),
        ("fm.ArchivedAlarm", "managed_object"),
        ("fm.ArchivedEvent", "managed_object"),
        ("fm.FailedEvent", "managed_object"),
        ("inv.Interface", "managed_object"),
        ("inv.SubInterface", "managed_object"),
        ("inv.ForwardingInstance", "managed_object"),
        ("sa.ManagedObject", "controller"),
        ("sla.SLAProbe", "managed_object"),
    ],
    delete=[
        ("sa.ManagedObjectAttribute", "managed_object"),
        ("sa.CPEStatus", "managed_object"),
        ("inv.MACDB", "managed_object"),
        ("sa.ServiceSummary", "managed_object"),
        ("inv.DiscoveryID", "object"),
        ("inv.Sensor", "managed_object"),
    ],
    clean=[
        ("ip.Address", "managed_object"),
        ("sa.Service", "managed_object"),
        ("maintenance.Maintenance", "escalate_managed_object"),
        ("maintenance.Maintenance", "direct_objects__object"),
    ],
)
class ManagedObject(NOCModel):
    """
    Managed Object
    """

    class Meta(object):
        verbose_name = "Managed Object"
        verbose_name_plural = "Managed Objects"
        db_table = "sa_managedobject"
        app_label = "sa"

    name = CharField("Name", max_length=64, unique=True)
    is_managed = BooleanField("Is Managed?", default=True)
    container: "Object" = DocumentReferenceField(Object, null=True, blank=True)
    administrative_domain: "AdministrativeDomain" = CachedForeignKey(
        AdministrativeDomain, verbose_name="Administrative Domain", on_delete=CASCADE
    )
    segment: "NetworkSegment" = DocumentReferenceField(NetworkSegment, null=False, blank=False)
    pool: "Pool" = DocumentReferenceField(Pool, null=False, blank=False)
    project = CachedForeignKey(
        Project, verbose_name="Project", on_delete=CASCADE, null=True, blank=True
    )
    # Optional pool to route FM events
    fm_pool = DocumentReferenceField(Pool, null=True, blank=True)
    profile: "Profile" = DocumentReferenceField(Profile, null=False, blank=False)
    vendor: "Vendor" = DocumentReferenceField(Vendor, null=True, blank=True)
    platform: "Platform" = DocumentReferenceField(Platform, null=True, blank=True)
    version: "Firmware" = DocumentReferenceField(Firmware, null=True, blank=True)
    # Firmware version to upgrade
    # Empty, when upgrade not scheduled
    next_version = DocumentReferenceField(Firmware, null=True, blank=True)
    object_profile: "ManagedObjectProfile" = CachedForeignKey(
        ManagedObjectProfile, verbose_name="Object Profile", on_delete=CASCADE
    )
    description = CharField("Description", max_length=256, null=True, blank=True)
    # Access
    auth_profile: "AuthProfile" = CachedForeignKey(
        AuthProfile, verbose_name="Auth Profile", null=True, blank=True, on_delete=CASCADE
    )
    scheme = IntegerField("Scheme", choices=SCHEME_CHOICES)
    address = CharField("Address", max_length=64)
    port = IntegerField("Port", blank=True, null=True)
    user = CharField("User", max_length=32, blank=True, null=True)
    password = CharField("Password", max_length=32, blank=True, null=True)
    super_password = CharField("Super Password", max_length=32, blank=True, null=True)
    remote_path = CharField("Path", max_length=256, blank=True, null=True)
    trap_source_type = CharField(
        max_length=1,
        choices=[
            ("d", "Disable"),
            ("m", "Management Address"),
            ("s", "Specify address"),
            ("l", "Loopback address"),
            ("a", "All interface addresses"),
        ],
        default="d",
        null=False,
        blank=False,
    )
    trap_source_ip = INETField("Trap Source IP", null=True, blank=True, default=None)
    syslog_source_type = CharField(
        max_length=1,
        choices=[
            ("d", "Disable"),
            ("m", "Management Address"),
            ("s", "Specify address"),
            ("l", "Loopback address"),
            ("a", "All interface addresses"),
        ],
        default="d",
        null=False,
        blank=False,
    )
    syslog_source_ip = INETField("Syslog Source IP", null=True, blank=True, default=None)
    trap_community = CharField("Trap Community", blank=True, null=True, max_length=64)
    snmp_ro = CharField("RO Community", blank=True, null=True, max_length=64)
    snmp_rw = CharField("RW Community", blank=True, null=True, max_length=64)
    snmp_rate_limit: int = IntegerField(default=0)
    access_preference = CharField(
        "CLI Privilege Policy",
        max_length=8,
        choices=[
            ("P", "Profile"),
            ("S", "SNMP Only"),
            ("C", "CLI Only"),
            ("SC", "SNMP, CLI"),
            ("CS", "CLI, SNMP"),
        ],
        default="P",
    )
    # IPAM
    fqdn: str = CharField("FQDN", max_length=256, null=True, blank=True)
    address_resolution_policy = CharField(
        "Address Resolution Policy",
        choices=[("P", "Profile"), ("D", "Disabled"), ("O", "Once"), ("E", "Enabled")],
        max_length=1,
        null=False,
        blank=False,
        default="P",
    )
    #
    l2_domain = DocumentReferenceField(L2Domain, null=True, blank=True)
    # CM
    config = GridVCSField("config")
    # Default VRF
    vrf = ForeignKey("ip.VRF", verbose_name="VRF", blank=True, null=True, on_delete=CASCADE)
    # Reference to controller, when object is CPE
    controller = ForeignKey(
        "self", verbose_name="Controller", blank=True, null=True, on_delete=CASCADE
    )
    # CPE id on given controller
    local_cpe_id = CharField("Local CPE ID", max_length=128, null=True, blank=True)
    # Globally unique CPE id
    global_cpe_id = CharField("Global CPE ID", max_length=128, null=True, blank=True)
    # Last seen date, for CPE
    last_seen = DateTimeField("Last Seen", blank=True, null=True)
    # Stencils
    shape = CharField(
        "Shape", blank=True, null=True, choices=stencil_registry.choices, max_length=128
    )
    shape_overlay_glyph = DocumentReferenceField(Glyph, null=True, blank=True)
    shape_overlay_position = CharField(
        "S.O. Position",
        max_length=2,
        choices=[(x.value, x.value) for x in ShapeOverlayPosition],
        null=True,
        blank=True,
    )
    shape_overlay_form = CharField(
        "S.O. Form",
        max_length=1,
        choices=[(x.value, x.value) for x in ShapeOverlayForm],
        null=True,
        blank=True,
    )
    #
    time_pattern = ForeignKey(TimePattern, null=True, blank=True, on_delete=SET_NULL)
    # Config processing handlers
    config_filter_handler: "Handler" = DocumentReferenceField(Handler, null=True, blank=True)
    config_diff_filter_handler: "Handler" = DocumentReferenceField(Handler, null=True, blank=True)
    config_validation_handler: "Handler" = DocumentReferenceField(Handler, null=True, blank=True)
    #
    max_scripts = IntegerField(
        "Max. Scripts", null=True, blank=True, help_text="Concurrent script session limits"
    )
    # Latitude and longitude, copied from container
    x = FloatField(null=True, blank=True)
    y = FloatField(null=True, blank=True)
    default_zoom = IntegerField(null=True, blank=True)
    # Software characteristics
    software_image = CharField("Software Image", max_length=255, null=True, blank=True)
    # Integration with external NRI and TT systems
    # Reference to remote system object has been imported from
    remote_system = DocumentReferenceField(RemoteSystem, null=True, blank=True)
    # Object id in remote system
    remote_id = CharField(max_length=64, null=True, blank=True)
    # Object id in BI
    bi_id = BigIntegerField(unique=True)
    # Object alarms can be escalated
    escalation_policy = CharField(
        "Escalation Policy",
        max_length=1,
        choices=[
            ("E", "Enable"),
            ("D", "Disable"),
            ("P", "From Profile"),
            ("R", "Escalate as depended"),
        ],
        default="P",
    )
    # Discovery running policy
    box_discovery_running_policy = CharField(
        "Box Running Policy",
        choices=[
            ("P", "From Profile"),
            ("R", "Require Up"),
            ("r", "Require if enabled"),
            ("i", "Ignore"),
        ],
        max_length=1,
        default="P",
    )
    periodic_discovery_running_policy = CharField(
        "Periodic Running Policy",
        choices=[
            ("P", "From Profile"),
            ("R", "Require Up"),
            ("r", "Require if enabled"),
            ("i", "Ignore"),
        ],
        max_length=1,
        default="P",
    )
    # Raise alarms on discovery problems
    box_discovery_alarm_policy = CharField(
        "Box Discovery Alarm Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "From Profile")],
        default="P",
    )
    periodic_discovery_alarm_policy = CharField(
        "Box Discovery Alarm Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "From Profile")],
        default="P",
    )
    # Telemetry settings
    box_discovery_telemetry_policy = CharField(
        "Box Discovery Telemetry Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "From Profile")],
        default="P",
    )
    box_discovery_telemetry_sample = IntegerField("Box Discovery Telemetry Sample", default=0)
    periodic_discovery_telemetry_policy = CharField(
        "Box Discovery Telemetry Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "From Profile")],
        default="P",
    )
    periodic_discovery_telemetry_sample = IntegerField("Box Discovery Telemetry Sample", default=0)
    # TT system for this object
    tt_system: "TTSystem" = DocumentReferenceField(TTSystem, null=True, blank=True)
    # TT system queue for this object
    tt_queue = CharField(max_length=64, null=True, blank=True)
    # Object id in tt system
    tt_system_id = CharField(max_length=64, null=True, blank=True)
    # CLI session policy
    cli_session_policy = CharField(
        "CLI Session Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "From Profile")],
        default="P",
    )
    # CLI privilege policy
    cli_privilege_policy = CharField(
        "CLI Privilege Policy",
        max_length=1,
        choices=[("E", "Raise privileges"), ("D", "Do not raise"), ("P", "From Profile")],
        default="P",
    )
    # Config policy
    config_policy = CharField(
        "Config Policy",
        max_length=1,
        choices=[
            ("P", "From Profile"),
            ("s", "Script"),
            ("S", "Script, Download"),
            ("D", "Download, Script"),
            ("d", "Download"),
        ],
        default="P",
    )
    config_fetch_policy = CharField(
        "Config Fetch Policy",
        max_length=1,
        choices=[("P", "From Profile"), ("s", "Startup"), ("r", "Running")],
        default="P",
    )
    # Interface discovery settings
    interface_discovery_policy = CharField(
        "Interface Discovery Policy",
        max_length=1,
        choices=[
            ("P", "From Profile"),
            ("s", "Script"),
            ("S", "Script, ConfDB"),
            ("C", "ConfDB, Script"),
            ("c", "ConfDB"),
        ],
        default="P",
    )
    # Caps discovery settings
    caps_discovery_policy = CharField(
        "Caps Discovery Policy",
        max_length=1,
        choices=[
            ("P", "From Profile"),
            ("s", "Script"),
            ("S", "Script, ConfDB"),
            ("C", "ConfDB, Script"),
            ("c", "ConfDB"),
        ],
        default="P",
    )
    # VLAN discovery settings
    vlan_discovery_policy = CharField(
        "VLAN Discovery Policy",
        max_length=1,
        choices=[
            ("P", "From Profile"),
            ("s", "Script"),
            ("S", "Script, ConfDB"),
            ("C", "ConfDB, Script"),
            ("c", "ConfDB"),
        ],
        default="P",
    )
    # Autosegmentation
    autosegmentation_policy = CharField(
        max_length=1,
        choices=[
            # Inherit from profile
            ("p", "Profile"),
            # Do not allow to move object by autosegmentation
            ("d", "Do not segmentate"),
            # Allow moving of object to another segment
            # by autosegmentation process
            ("e", "Allow autosegmentation"),
            # Move seen objects to this object's segment
            ("o", "Segmentate to existing segment"),
            # Expand autosegmentation_segment_name template,
            # ensure that children segment with same name exists
            # then move seen objects to this segment.
            # Following context variables are availale:
            # * object - this object
            # * interface - interface on which remote_object seen from object
            # * remote_object - remote object name
            # To create single segment use templates like {{object.name}}
            # To create segments on per-interface basic use
            # names like {{object.name}}-{{interface.name}}
            ("c", "Segmentate to child segment"),
        ],
        default="p",
    )
    #
    event_processing_policy = CharField(
        "Event Processing Policy",
        max_length=1,
        choices=[("P", "Profile"), ("E", "Process Events"), ("D", "Drop events")],
        default="P",
    )
    # Collect and archive syslog events
    syslog_archive_policy = CharField(
        "SYSLOG Archive Policy",
        max_length=1,
        choices=[("E", "Enable"), ("D", "Disable"), ("P", "Profile")],
        default="P",
    )
    # Behavior on denied firmware detection
    denied_firmware_policy = CharField(
        "Firmware Policy",
        max_length=1,
        choices=[
            ("P", "Profile"),
            ("I", "Ignore"),
            ("s", "Ignore&Stop"),
            ("A", "Raise Alarm"),
            ("S", "Raise Alarm&Stop"),
        ],
        default="P",
    )
    # ConfDB settings
    confdb_raw_policy = CharField(
        "ConfDB Raw Policy",
        max_length=1,
        choices=[("P", "Profile"), ("D", "Disable"), ("E", "Enable")],
        default="P",
    )
    # Dynamic Profile Classification
    dynamic_classification_policy = CharField(
        "Dynamic Classification Policy",
        max_length=1,
        choices=[("P", "Profile"), ("D", "Disable"), ("R", "By Rule")],
        default="P",
    )
    # Resource groups
    static_service_groups = ObjectIDArrayField(db_index=True, blank=True, null=True, default=list)
    effective_service_groups = ObjectIDArrayField(
        db_index=True, blank=True, null=True, default=list
    )
    static_client_groups = ObjectIDArrayField(db_index=True, blank=True, null=True, default=list)
    effective_client_groups = ObjectIDArrayField(db_index=True, blank=True, null=True, default=list)
    #
    labels = ArrayField(CharField(max_length=250), blank=True, null=True, default=list)
    effective_labels = ArrayField(CharField(max_length=250), blank=True, null=True, default=list)
    #
    caps: List[Dict[str, Any]] = PydanticField(
        "Caps Items",
        schema=CapsItems,
        blank=True,
        null=True,
        default=list,
        # ? Internal validation not worked with JSON Field
        # validators=[match_rules_validate],
    )
    # Additional data
    uplinks = ArrayField(IntegerField(), blank=True, null=True, default=list)
    links = ArrayField(IntegerField(), blank=True, null=True, default=list, db_index=True)
    # RCA neighbors cache
    rca_neighbors = ArrayField(IntegerField(), blank=True, null=True, default=list)
    # xRCA donwlink merge window settings
    # for rca_neighbors.
    # Each position represents downlink merge windows for each rca neighbor.
    # Windows are in seconds, 0 - downlink merge is disabled
    dlm_windows = ArrayField(IntegerField(), blank=True, null=True, default=list)
    # Paths
    adm_path = ArrayField(IntegerField(), blank=True, null=True, default=list)
    segment_path = ObjectIDArrayField(db_index=True, blank=True, null=True, default=list)
    container_path = ObjectIDArrayField(db_index=True, blank=True, null=True, default=list)
    affected_maintenances: Dict[str, Dict[str, str]] = PydanticField(
        "Maintenance Items",
        schema=MaintenanceItems,
        blank=True,
        null=True,
        default=dict,
        # ? Internal validation not worked with JSON Field
        # validators=[match_rules_validate],
    )
    diagnostics: Dict[str, DiagnosticItem] = PydanticField(
        "Diagnostic Items",
        schema=DiagnosticItems,
        blank=True,
        null=True,
        default=dict,
    )

    # Event ids
    EV_CONFIG_CHANGED = "config_changed"  # Object's config changed
    EV_ALARM_RISEN = "alarm_risen"  # New alarm risen
    EV_ALARM_REOPENED = "alarm_reopened"  # Alarm has been reopen
    EV_ALARM_CLEARED = "alarm_cleared"  # Alarm cleared
    EV_ALARM_COMMENTED = "alarm_commented"  # Alarm commented
    EV_NEW = "object_new"  # New object created
    EV_DELETED = "object_deleted"  # Object deleted
    EV_VERSION_CHANGED = "version_changed"  # Version changed
    EV_INTERFACE_CHANGED = "interface_changed"  # Interface configuration changed
    EV_SCRIPT_FAILED = "script_failed"  # Script error
    EV_CONFIG_POLICY_VIOLATION = "config_policy_violation"  # Policy violations found

    PROFILE_LINK = "object_profile"

    BOX_DISCOVERY_JOB = "noc.services.discovery.jobs.box.job.BoxDiscoveryJob"
    PERIODIC_DISCOVERY_JOB = "noc.services.discovery.jobs.periodic.job.PeriodicDiscoveryJob"

    _id_cache = cachetools.TTLCache(maxsize=1000, ttl=60)
    _bi_id_cache = cachetools.TTLCache(maxsize=1000, ttl=60)
    _e_labels_cache = cachetools.TTLCache(maxsize=1000, ttl=60)
    _neighbor_cache = cachetools.TTLCache(1000, ttl=300)

    _ignore_on_save = (
        "caps",
        "uplinks",
        "links",
        "rca_neighbors",
        "dlm_windows",
        "adm_path",
        "segment_path",
        "container_path",
        "affected_maintenances",
        "diagnostics",
    )
    # Access affected fields
    _access_fields = {
        "scheme",
        "address",
        "port",
        "auth_profile",
        "object_profile",
        "user",
        "password",
        "super_password",
        "snmp_ro",
        "snmp_rw",
        "access_preference",
        "cli_privilege_policy",
    }

    def __str__(self):
        return self.name

    @classmethod
    @cachedmethod(
        operator.attrgetter("_id_cache"),
        key="managedobject-id-%s",
        lock=lambda _: id_lock,
        version=MANAGEDOBJECT_CACHE_VERSION,
    )
    def get_by_id(cls, oid: int) -> "Optional[ManagedObject]":
        """
        Get ManagedObject by id. Cache returned instance for future use.

        :param oid: Managed Object's id
        :return: ManagedObject instance
        """
        mo = ManagedObject.objects.filter(id=oid)[:1]
        if mo:
            return mo[0]
        return None

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_bi_id_cache"), lock=lambda _: id_lock)
    def get_by_bi_id(cls, bi_id) -> "Optional[ManagedObject]":
        mo = ManagedObject.objects.filter(bi_id=bi_id)[:1]
        if mo:
            return mo[0]
        else:
            return None

    def iter_changed_datastream(self, changed_fields=None):
        changed_fields = set(changed_fields or [])
        if config.datastream.enable_managedobject:
            yield "managedobject", self.id
        if config.datastream.enable_cfgping and changed_fields.intersection(
            {
                "id",  # Create object
                "name",
                "bi_id",
                "is_managed",
                "pool",
                "fm_pool",
                "address",
                "object_profile",
                "time_pattern",
                "event_processing_policy",
            }
        ):
            yield "cfgping", self.id
        if config.datastream.enable_cfgsyslog and changed_fields.intersection(
            {
                "id",  # Create object
                "name",
                "bi_id",
                "is_managed",
                "pool",
                "fm_pool",
                "address",
                "object_profile",
                "event_processing_policy",
                "syslog_archive_policy",
                "syslog_source_type",
                "syslog_source_ip",
            }
        ):
            yield "cfgsyslog", self.id
        if config.datastream.enable_cfgtrap and changed_fields.intersection(
            {
                "id",  # Create object
                "name",
                "bi_id",
                "is_managed",
                "pool",
                "fm_pool",
                "address",
                "object_profile",
                "event_processing_policy",
                "trap_source_type",
                "trap_source_ip",
            }
        ):
            yield "cfgtrap", self.id
        if config.datastream.enable_cfgmetricsources and changed_fields.intersection(
            {"id", "bi_id", "is_managed", "pool", "fm_pool", "labels", "effective_labels"}
        ):
            yield "cfgmetricsources", f"sa.ManagedObject::{self.bi_id}"

    def set_scripts_caller(self, caller):
        """
        Override default scripts caller
        :param caller: callabler
        :return:
        """
        self._scripts_caller = caller

    @property
    def scripts(self):
        sp = getattr(self, "_scripts", None)
        if sp:
            return sp
        self._scripts = ScriptsProxy(self, getattr(self, "_scripts_caller", None))
        return self._scripts

    @property
    def actions(self):
        return ActionsProxy(self)

    @property
    def matchers(self):
        mp = getattr(self, "_matchers", None)
        if mp:
            return mp
        self._matchers = MatchersProxy(self)
        return self._matchers

    def reset_matchers(self):
        self._matchers = None

    @classmethod
    def user_objects(cls, user):
        """
        Get objects available to user

        :param user: User
        :type user: User instance
        :rtype: Queryset instance
        """
        return cls.objects.filter(UserAccess.Q(user))

    def has_access(self, user):
        """
        Check user has access to object

        :param user: User
        :type user: User instance
        :rtype: Bool
        """
        if user.is_superuser:
            return True
        return self.user_objects(user).filter(id=self.id).exists()

    @property
    def granted_users(self):
        """
        Get list of user granted access to object

        :rtype: List of User instancies
        """
        return [
            u
            for u in User.objects.filter(is_active=True)
            if ManagedObject.objects.filter(UserAccess.Q(u) & Q(id=self.id)).exists()
        ]

    @property
    def granted_groups(self):
        """
        Get list of groups granted access to object

        :rtype: List of Group instancies
        """
        return [
            g
            for g in Group.objects.filter()
            if ManagedObject.objects.filter(GroupAccess.Q(g) & Q(id=self.id)).exists()
        ]

    @classmethod
    def get_component(
        cls, managed_object: "ManagedObject", mac=None, ipv4=None, vrf=None, **kwargs
    ) -> Optional["ManagedObject"]:
        from noc.inv.models.subinterface import SubInterface
        from noc.inv.models.forwardinginstance import ForwardingInstance
        from noc.inv.models.discoveryid import DiscoveryID

        if mac:
            mac = MACAddressParameter().clean(mac)
            return DiscoveryID.find_object(mac)
        if ipv4:
            q = {"ipv4_addresses": ipv4}
            if vrf is not None and vrf != "default":
                fi = list(ForwardingInstance.objects.filter(name=vrf)[:2])
                if len(fi) == 1:
                    q["forwarding_instance"] = fi[0]
            si = list(SubInterface.objects.filter(**q)[:2])
            if len(si) == 1:
                return si[0].managed_object

    def on_save(self):
        # Invalidate caches
        deleted_cache_keys = ["managedobject-name-to-id-%s" % self.name]
        diagnostics = []
        # Notify new object
        if not self.initial_data["id"]:
            self.event(self.EV_NEW)
        # Remove discovery jobs from old pool
        if "pool" in self.changed_fields and self.initial_data["id"]:
            pool_name = Pool.get_by_id(self.initial_data["pool"].id).name
            Job.remove("discovery", self.BOX_DISCOVERY_JOB, key=self.id, pool=pool_name)
            Job.remove("discovery", self.PERIODIC_DISCOVERY_JOB, key=self.id, pool=pool_name)
        # Reset matchers
        if (
            "vendor" in self.changed_fields
            or "platform" in self.changed_fields
            or "version" in self.changed_fields
            or "software_image" in self.changed_fields
        ):
            self.reset_matchers()
        # Invalidate credentials cache
        if (
            self.initial_data["id"] is None
            or self._access_fields.intersection(set(self.changed_fields))
            or "profile" in self.changed_fields
            or "vendor" in self.changed_fields
            or "platform" in self.changed_fields
            or "version" in self.changed_fields
            or "pool" in self.changed_fields
            or "remote_path" in self.changed_fields
            or "snmp_rate_limit" in self.changed_fields
        ):
            cache.delete("cred-%s" % self.id, version=CREDENTIAL_CACHE_VERSION)
        if self.initial_data["id"] is None or self._access_fields.intersection(
            set(self.changed_fields)
        ):
            diagnostics += ["CLI", "Access"]
        if (
            "auth_profile" in self.changed_fields
            or "snmp_ro" in self.changed_fields
            or "snmp_rw" in self.changed_fields
            or "address" in self.changed_fields
        ):
            diagnostics += ["SNMP"]
        # Rebuild paths
        if (
            self.initial_data["id"] is None
            or "administrative_domain" in self.changed_fields
            or "segment" in self.changed_fields
            or "container" in self.changed_fields
        ):
            self.adm_path = self.administrative_domain.get_path()
            self.segment_path = [str(sid) for sid in self.segment.get_path()]
            self.container_path = (
                [str(sid) for sid in self.container.get_path()] if self.container else []
            )
            ManagedObject.objects.filter(id=self.id).update(
                adm_path=self.adm_path,
                segment_path=self.segment_path,
                container_path=self.container_path,
            )
            if self.container and "container" in self.changed_fields:
                x, y, zoom = self.container.get_coordinates_zoom()
                ManagedObject.objects.filter(id=self.id).update(x=x, y=y, default_zoom=zoom)
        if self.initial_data["id"] and "container" in self.changed_fields:
            # Move object to another container
            if self.container:
                for o in Object.get_managed(self):
                    o.container = self.container.id
                    o.log("Moved to container %s (%s)" % (self.container, self.container.id))
                    o.save()
        # Rebuild summary
        if "object_profile" in self.changed_fields:
            NetworkSegment.update_summary(self.segment)
        # Apply discovery jobs
        self.ensure_discovery_jobs()
        #
        self._reset_caches(self.id, credential=True)
        cache.delete_many(deleted_cache_keys)
        # Rebuild segment access
        if self.initial_data["id"] is None:
            self.segment.update_access()
        elif "segment" in self.changed_fields:
            iseg = self.initial_data["segment"]
            if iseg and isinstance(iseg, str):
                iseg = NetworkSegment.get_by_id(iseg)
            if iseg:
                iseg.update_access()
                iseg.update_uplinks()
            self.segment.update_access()
            self.update_topology()
            # Refresh links
            from noc.inv.models.link import Link

            for ll in Link.object_links(self):
                ll.save()
        # Handle became unmanaged
        if (
            not self.initial_data["id"] is None
            and "is_managed" in self.changed_fields
            and not self.is_managed
        ):
            # Clear alarms
            from noc.fm.models.activealarm import ActiveAlarm

            for aa in ActiveAlarm.objects.filter(managed_object=self.id):
                aa.clear_alarm("Management is disabled")
            # Clear discovery id
            from noc.inv.models.discoveryid import DiscoveryID

            DiscoveryID.clean_for_object(self)
        if "effective_labels" in self.changed_fields:
            # Update configured diagnostic
            self.update_diagnostics()
        # Update configured state on diagnostics
        if diagnostics:
            # Reset changed diagnostic
            self.reset_diagnostic(diagnostics)
            # Update complex diagnostics
            self.update_diagnostics()

    def on_delete(self):
        # Reset discovery cache
        from noc.inv.models.discoveryid import DiscoveryID

        DiscoveryID.clean_for_object(self)
        self._reset_caches(self.id, credential=True)
        self.event(self.EV_DELETED)

    def get_index(self):
        """
        Get FTS index
        """
        card = f"Managed object {self.name} ({self.address})"
        content: List[str] = [self.name, self.address]
        if self.trap_source_ip:
            content += [self.trap_source_ip]
        platform = self.platform
        if platform:
            content += [smart_text(platform.name)]
            card += " [%s]" % platform.name
        version = str(self.version)
        if version:
            content += [version]
            card += " version %s" % version
        if self.description:
            content += [self.description]
        config = self.config.read()
        if config:
            if len(config) > 10000000:
                content += [config[:10000000]]
            else:
                content += [config]
        r = {"title": self.name, "content": "\n".join(content), "card": card, "tags": self.labels}
        return r

    @classmethod
    def get_search_result_url(cls, obj_id):
        return "/api/card/view/managedobject/%s/" % obj_id

    @property
    def is_router(self):
        """
        Returns True if Managed Object presents in more than one networks
        :return:
        """
        # @todo: Rewrite
        return self.address_set.count() > 1

    def get_attr(self, name, default=None):
        """
        Return attribute as string
        :param name:
        :param default:
        :return:
        """
        warnings.warn(
            "Capability should be used instead of Attributes."
            " Will be strict requirement in NOC 23.1",
            RemovedInNOC2301Warning,
        )
        try:
            return self.managedobjectattribute_set.get(key=name).value
        except ManagedObjectAttribute.DoesNotExist:
            return default

    def get_attr_bool(self, name, default=False):
        """
        Return attribute as bool
        :param name:
        :param default:
        :return:
        """
        v = self.get_attr(name)
        if v is None:
            return default
        if v.lower() in ["t", "true", "y", "yes", "1"]:
            return True
        else:
            return False

    def get_attr_int(self, name, default=0):
        """
        Return attribute as integer
        :param name:
        :param default:
        :return:
        """
        v = self.get_attr(name)
        if v is None:
            return default
        try:
            return int(v)
        except:  # noqa
            return default

    def set_attr(self, name, value):
        """
        Set attribute
        :param name:
        :param value:
        :return:
        """
        value = smart_text(value)
        try:
            v = self.managedobjectattribute_set.get(key=name)
            v.value = value
        except ManagedObjectAttribute.DoesNotExist:
            v = ManagedObjectAttribute(managed_object=self, key=name, value=value)
        v.save()

    def update_attributes(self, attr):
        warnings.warn(
            "Capability should be used instead of Attributes."
            " Will be strict requirement in NOC 23.1",
            RemovedInNOC2301Warning,
        )
        for k in attr:
            v = attr[k]
            ov = self.get_attr(k)
            if ov != v:
                self.set_attr(k, v)
                logger.info("%s: %s -> %s", k, ov, v)

    def is_ignored_interface(self, interface):
        interface = self.get_profile().convert_interface_name(interface)
        rx = self.get_attr("ignored_interfaces")
        if rx:
            return re.match(rx, interface) is not None
        return False

    def get_status(self):
        return ObjectStatus.get_status(self)

    def get_last_status(self):
        return ObjectStatus.get_last_status(self)

    def set_status(self, status, ts=None):
        """
        Update managed object status
        :param status: new status
        :param ts: status change time
        :return: False if out-of-order update, True otherwise
        """
        return ObjectStatus.set_status(self, status, ts=ts)

    def get_inventory(self):
        """
        Retuns a list of inventory Objects managed by
        this managed object
        """
        from noc.inv.models.object import Object

        return list(
            Object.objects.filter(
                data__match={"interface": "management", "attr": "managed_object", "value": self.id}
            )
        )

    def run_discovery(self, delta=0):
        """
        Schedule box discovery
        """
        if not self.object_profile.enable_box_discovery or not self.is_managed:
            return
        logger.debug("[%s] Scheduling box discovery after %ds", self.name, delta)
        Job.submit(
            "discovery",
            self.BOX_DISCOVERY_JOB,
            key=self.id,
            pool=self.pool.name,
            delta=delta or self.pool.get_delta(),
        )

    def event(self, event_id: str, data: Optional[Dict[str, Any]] = None, delay=None, tag=None):
        """
        Process object-related event
        :param event_id: ManagedObject.EV_*
        :param data: Event context to render
        :param delay: Notification delay in seconds
        :param tag: Notification tag
        """
        logger.debug("[%s|%s] Sending object event message: %s", self.name, event_id, data)
        data = data or {}
        data.update({"managed_object": self.get_message_context()})
        send_message(
            data=data,
            message_type=event_id,
            headers={
                MX_LABELS: MX_H_VALUE_SPLITTER.join(self.effective_labels).encode(
                    encoding=DEFAULT_ENCODING
                ),
                MX_ADMINISTRATIVE_DOMAIN_ID: str(self.administrative_domain.id).encode(
                    encoding=DEFAULT_ENCODING
                ),
            },
        )

        # Schedule FTS reindex
        if event_id in (self.EV_CONFIG_CHANGED, self.EV_VERSION_CHANGED):
            TextIndex.update_index(ManagedObject, self)

    def save_config(self, data, validate=True):
        """
        Save new configuration to GridVCS
        :param data: config
        :param validate: Run config validation
        :return: True if config has been changed, False otherwise
        """
        if isinstance(data, list):
            # Convert list to plain text
            r = []
            for d in sorted(data, key=operator.itemgetter("name")):
                r += [
                    "==[ %s ]========================================\n%s"
                    % (d["name"], d["config"])
                ]
            data = "\n".join(r)
        # Wipe out unnecessary parts
        if self.config_filter_handler:
            if self.config_filter_handler.allow_config_filter:
                handler = self.config_filter_handler.get_handler()
                data = handler(self, data) or ""
            else:
                logger.warning("Handler is not allowed for config filter")
        # Pass data through config filter, if given
        if self.config_diff_filter_handler:
            if self.config_diff_filter_handler.allow_config_diff_filter:
                handler = self.config_diff_filter_handler.get_handler()
                data = handler(self, data) or ""
            else:
                logger.warning("Handler is not allowed for config diff filter")
        # Pass data through the validation filter, if given
        # @todo: Replace with config validation policy
        if self.config_validation_handler:
            if self.config_validation_handler.allow_config_validation:
                handler = self.config_validation_handler.get_handler()
                warnings = handler(self, data)
                if warnings:
                    # There are some warnings. Notify responsible persons
                    self.event(self.EV_CONFIG_POLICY_VIOLATION, {"warnings": warnings})
            else:
                logger.warning("Handler is not allowed for config validation")
        # Calculate diff
        old_data = self.config.read()
        is_new = not bool(old_data)
        diff = None
        if is_new:
            changed = True
        else:
            # Calculate diff
            if self.config_diff_filter_handler:
                if self.config_diff_filter_handler.allow_config_diff_filter:
                    handler = self.config_diff_filter_handler.get_handler()
                    # Pass through filters
                    old_data = handler(self, old_data)
                    new_data = handler(self, data)
                    if not old_data and not new_data:
                        logger.error(
                            "[%s] broken config_diff_filter: Returns empty result", self.name
                        )
                else:
                    self.logger.warning("Handler is not allowed for config diff filter")
                    new_data = data
            else:
                new_data = data
            changed = old_data != new_data
            if changed:
                diff = "".join(
                    difflib.unified_diff(
                        old_data.splitlines(True),
                        new_data.splitlines(True),
                        fromfile=os.path.join("a", smart_text(self.name)),
                        tofile=os.path.join("b", smart_text(self.name)),
                    )
                )
        if changed:
            # Notify changes
            self.notify_config_changes(is_new=is_new, data=data, diff=diff)
            # Save config
            self.write_config(data)
        # Apply mirroring settings
        self.mirror_config(data, changed)
        # Apply changes if necessary
        if changed:
            change_tracker.register("update", "sa.ManagedObject", str(self.id), fields=[])
        return changed

    def notify_config_changes(self, is_new, data, diff):
        """
        Notify about config changes
        :param is_new:
        :param data:
        :param diff:
        :return:
        """
        self.event(self.EV_CONFIG_CHANGED, {"is_new": is_new, "config": data, "diff": diff})

    def write_config(self, data):
        """
        Save config to GridVCS
        :param data: Config data
        :return:
        """
        logger.debug("[%s] Writing config", self.name)
        self.config.write(data)

    def mirror_config(self, data, changed):
        """
        Save config to mirror
        :param data: Config data
        :param changed: True if config has been changed
        :return:
        """
        logger.debug("[%s] Mirroring config", self.name)
        policy = self.object_profile.config_mirror_policy
        # D - Disable
        if policy == "D":
            logger.debug("[%s] Mirroring is disabled by policy. Skipping", self.name)
            return
        # C - Mirror on Change
        if policy == "C" and not changed:
            logger.debug("[%s] Configuration has not been changed. Skipping", self.name)
            return
        # Check storage
        storage = self.object_profile.config_mirror_storage
        if not storage:
            logger.debug("[%s] Storage is not configured. Skipping", self.name)
            return
        if not storage.is_config_mirror:
            logger.debug(
                "[%s] Config mirroring is disabled for storage '%s'. Skipping",
                self.name,
                storage.name,
            )
            return  # No storage setting
        # Check template
        template = self.object_profile.config_mirror_template
        if not template:
            logger.debug("[%s] Path template is not configured. Skipping", self.name)
            return
        # Render path
        path = self.object_profile.config_mirror_template.render_subject(
            object=self, datetime=datetime
        ).strip()
        if not path:
            logger.debug("[%s] Empty mirror path. Skipping", self.name)
            return
        logger.debug(
            "[%s] Mirroring to %s:%s",
            self.name,
            self.object_profile.config_mirror_storage.name,
            path,
        )
        dir_path = os.path.dirname(path)
        try:
            with storage.open_fs() as fs:
                if dir_path and dir_path != "/" and not fs.isdir(dir_path):
                    logger.debug("[%s] Ensuring directory: %s", self.name, dir_path)
                    fs.makedirs(dir_path, recreate=True)
                logger.debug("[%s] Mirroring %d bytes", self.name, len(data))
                fs.writebytes(path, data.encode(encoding=DEFAULT_ENCODING))
        except storage.Error as e:
            logger.error("[%s] Failed to mirror config: %s", self.name, e)

    def to_validate(self, changed):
        """
        Check if config is to be validated

        :param changed: True if config has been changed
        :return: Boolean
        """
        policy = self.object_profile.config_validation_policy
        # D - Disable
        if policy == "D":
            logger.debug("[%s] Validation is disabled by policy. Skipping", self.name)
            return False
        # C - Validate on Change
        if policy == "C" and not changed:
            logger.debug("[%s] Configuration has not been changed. Skipping", self.name)
            return False
        return True

    def iter_validation_problems(self, changed: bool) -> Iterable[ProblemItem]:
        """
        Yield validation problems

        :param changed: True if config has been changed
        :return:
        """
        logger.debug("[%s] Validating config", self.name)
        if not self.to_validate(changed):
            return
        confdb = self.get_confdb()
        # Object-level validation
        if self.object_profile.object_validation_policy:
            yield from self.object_profile.object_validation_policy.iter_problems(confdb)
        else:
            logger.debug("[%s] Object validation policy is not set. Skipping", self.name)
        # Interface-level validation
        from noc.inv.models.interface import Interface
        from noc.inv.models.interfaceprofile import InterfaceProfile

        for doc in Interface._get_collection().aggregate(
            [
                {"$match": {"managed_object": self.id}},
                {"$project": {"_id": 0, "name": 1, "profile": 1}},
                {"$group": {"_id": "$profile", "ifaces": {"$push": "$name"}}},
            ]
        ):
            iprofile = InterfaceProfile.get_by_id(doc["_id"])
            if not iprofile or not iprofile.interface_validation_policy:
                continue
            for ifname in doc["ifaces"]:
                for problem in iprofile.interface_validation_policy.iter_problems(
                    confdb, ifname=ifname
                ):
                    yield problem

    @property
    def credentials(self) -> Credentials:
        """
        Get effective credentials
        """
        if self.auth_profile:
            return Credentials(
                user=self.auth_profile.user,
                password=self.auth_profile.password,
                super_password=self.auth_profile.super_password,
                snmp_ro=self.auth_profile.snmp_ro or self.snmp_ro,
                snmp_rw=self.auth_profile.snmp_rw or self.snmp_rw,
                snmp_rate_limit=self.get_effective_snmp_rate_limit(),
            )
        else:
            return Credentials(
                user=self.user,
                password=self.password,
                super_password=self.super_password,
                snmp_ro=self.snmp_ro,
                snmp_rw=self.snmp_rw,
                snmp_rate_limit=self.get_effective_snmp_rate_limit(),
            )

    @property
    def scripts_limit(self):
        ol = self.max_scripts or None
        pl = self.profile.max_scripts
        if not ol:
            return pl
        if pl:
            return min(ol, pl)
        else:
            return ol

    def iter_recursive_objects(self):
        """
        Generator yielding all recursive objects
        for effective PM settings
        """
        from noc.inv.models.interface import Interface

        yield from Interface.objects.filter(managed_object=self.id)

    def get_caps(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns a dict of effective object capabilities
        """

        caps = {}
        scope = scope or ""
        if self.caps:
            for c in self.caps:
                cc = Capability.get_by_id(c["capability"])
                if not cc or (scope and c.get("scope", "") != scope):
                    continue
                caps[cc.name] = c.get("value")
        return caps

    def save(self, **kwargs):
        kwargs = kwargs or {}
        if getattr(self, "_allow_update_fields", None) and "update_fields" not in kwargs:
            kwargs["update_fields"] = self._allow_update_fields
        super().save(**kwargs)

    def update_caps(
        self, caps: Dict[str, Any], source: str, scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update existing capabilities with a new ones.
        :param caps: dict of caps name -> caps value
        :param source: Source name
        :param scope: Scope name
        """

        o_label = f"{scope or ''}{self.name}|{source}"
        # Update existing capabilities
        new_caps = []
        seen = set()
        changed = False
        for ci in self.caps:
            c = Capability.get_by_id(ci["capability"])
            cs = ci.get("source")
            css = ci.get("scope", "")
            cv = ci.get("value")
            if not c:
                logger.info("[%s] Removing unknown capability id %s", o_label, ci["capability"])
                continue
            cv = c.clean_value(cv)
            cn = c.name
            seen.add(cn)
            if scope and scope != css:
                logger.info(
                    "[%s] Not changing capability %s: from other scope '%s'",
                    o_label,
                    cn,
                    css,
                )
            elif cs == source:
                if cn in caps:
                    if caps[cn] != cv:
                        logger.info(
                            "[%s] Changing capability %s: %s -> %s", o_label, cn, cv, caps[cn]
                        )
                        ci["value"] = caps[cn]
                        changed = True
                else:
                    logger.info("[%s] Removing capability %s", o_label, cn)
                    changed = True
                    continue
            elif cn in caps:
                logger.info(
                    "[%s] Not changing capability %s: Already set with source '%s'",
                    o_label,
                    cn,
                    cs,
                )
            new_caps += [ci]
        # Add new capabilities
        for cn in set(caps) - seen:
            c = Capability.get_by_name(cn)
            if not c:
                logger.info("[%s] Unknown capability %s, ignoring", o_label, cn)
                continue
            logger.info("[%s] Adding capability %s = %s", o_label, cn, caps[cn])
            new_caps += [{"capability": str(c.id), "value": caps[cn], "source": source}]
            changed = True

        if changed:
            logger.info("[%s] Saving changes", o_label)
            from django.db import connection

            self.caps = new_caps
            cursor = connection.cursor()
            cursor.execute(
                f"""UPDATE {self._meta.db_table} SET caps = %s::jsonb WHERE id = {self.id}""",
                [smart_text(orjson.dumps(new_caps))],
            )
            # self.save()
            self._reset_caches(self.id, credential=True)
        caps = {}
        for ci in new_caps:
            cn = Capability.get_by_id(ci["capability"])
            if cn:
                caps[cn.name] = ci.get("value")
        return caps

    def set_caps(
        self, key: str, value: Any, source: str = "manual", scope: Optional[str] = ""
    ) -> None:
        caps = Capability.get_by_name(key)
        value = caps.clean_value(value)
        for item in self.caps:
            if item["capability"] == str(caps.id):
                if not scope or item.get("scope", "") == scope:
                    item["value"] = value
                    break
        else:
            # Insert new item
            self.caps += [
                {"capability": str(caps.id), "value": value, "source": source, "scope": scope or ""}
            ]

    def disable_discovery(self):
        """
        Disable all discovery methods related with managed object
        """

    def get_profile(self):
        """
        Getting profile methods
        Exa:
         mo.get_profile().convert_interface_name(i)
        :return:
        """
        profile = getattr(self, "_profile", None)
        if not profile:
            self._profile = self.profile.get_profile()
        return self._profile

    def get_interface(self, name):
        from noc.inv.models.interface import Interface

        name = self.get_profile().convert_interface_name(name)
        try:
            return Interface.objects.get(managed_object=self.id, name=name)
        except Interface.DoesNotExist:
            pass
        for n in self.get_profile().get_interface_names(name):
            try:
                return Interface.objects.get(managed_object=self.id, name=n)
            except Interface.DoesNotExist:
                pass
        return None

    def get_linecard(self, ifname):
        """
        Returns linecard number related to interface
        :param ifname:
        :return:
        """
        return self.get_profile().get_linecard(ifname)

    def ensure_discovery_jobs(self):
        """
        Check and schedule discovery jobs
        """
        if self.is_managed and self.object_profile.enable_box_discovery:
            Job.submit(
                "discovery",
                self.BOX_DISCOVERY_JOB,
                key=self.id,
                pool=self.pool.name,
                delta=self.pool.get_delta(),
                keep_ts=True,
            )
        else:
            Job.remove("discovery", self.BOX_DISCOVERY_JOB, key=self.id, pool=self.pool.name)
            self.reset_diagnostic([PROFILE_DIAG, SNMP_DIAG, CLI_DIAG])
        if self.is_managed and self.object_profile.enable_periodic_discovery:
            Job.submit(
                "discovery",
                self.PERIODIC_DISCOVERY_JOB,
                key=self.id,
                pool=self.pool.name,
                delta=self.pool.get_delta(),
                keep_ts=True,
            )
        else:
            Job.remove("discovery", self.PERIODIC_DISCOVERY_JOB, key=self.id, pool=self.pool.name)

    def update_topology(self):
        """
        Rebuild topology caches
        """
        self.segment.update_uplinks()
        # Rebuild PoP links
        container = self.container
        for o in Object.get_managed(self):
            pop = o.get_pop()
            if not pop and container:
                # Fallback to MO container
                pop = container.get_pop()
            if pop:
                call_later("noc.inv.util.pop_links.update_pop_links", 20, pop_id=pop.id)

    @classmethod
    def get_search_Q(cls, query):
        """
        Filters type:
        #1 IP address regexp - if .* in query
        #2 Name regexp - if "+*[]()" in query
        #3 IPv4 query - if query is valid IPv4 address
        #4 IPv4 prefix - if query is valid prefix from /16 to /32 (192.168.0.0/16, 192.168.0.0/g, 192.168.0.0/-1)
        #5 Discovery ID query - Find on MAC Discovery ID
        :param query: Query from __query request field
        :return: Django Q filter (Use it: ManagedObject.objects.filter(q))
        """
        query = query.strip()
        if query:
            if ".*" in query and is_ipv4(query.replace(".*", ".1")):
                return Q(address__regex=query.replace(".", "\\.").replace("*", "[0-9]+"))
            elif set("+*[]()") & set(query):
                # Maybe regular expression
                try:
                    # Check syntax
                    # @todo: PostgreSQL syntax differs from python one
                    re.compile(query)
                    return Q(name__regex=query)
                except re.error:
                    pass
            elif is_ipv4(query):
                # Exact match on IP address
                return Q(address=query)
            elif is_ipv4_prefix(query):
                # Match by prefix
                p = IP.prefix(query)
                return SQL("cast_test_to_inet(address) <<= '%s'" % p)
            else:
                try:
                    mac = MACAddressParameter().clean(query)
                    from noc.inv.models.discoveryid import DiscoveryID

                    mo = DiscoveryID.find_all_objects(mac)
                    if mo:
                        return Q(id__in=mo)
                except ValueError:
                    pass
        return None

    def open_session(self, idle_timeout=None):
        return SessionContext(self, idle_timeout)

    def can_escalate(self, depended=False):
        """
        Check alarm can be escalated
        :return:
        """
        if not self.tt_system or not self.tt_system_id:
            return False
        return self.can_notify(depended)

    def can_notify(self, depended=False):
        """
        Check alarm can be notified via escalation
        :param depended:
        :return:
        """
        if self.escalation_policy == "E":
            return True
        elif self.escalation_policy == "P":
            return self.object_profile.can_escalate(depended)
        elif self.escalation_policy == "R":
            return bool(depended)
        else:
            return False

    def can_create_box_alarms(self):
        if self.box_discovery_alarm_policy == "E":
            return True
        elif self.box_discovery_alarm_policy == "P":
            return self.object_profile.can_create_box_alarms()
        else:
            return False

    def can_create_periodic_alarms(self):
        if self.periodic_discovery_alarm_policy == "E":
            return True
        elif self.periodic_discovery_alarm_policy == "P":
            return self.object_profile.can_create_periodic_alarms()
        else:
            return False

    def can_cli_session(self):
        if self.cli_session_policy == "E":
            return True
        elif self.cli_session_policy == "P":
            return self.object_profile.can_cli_session()
        else:
            return False

    @property
    def box_telemetry_sample(self):
        if self.box_discovery_telemetry_policy == "E":
            return self.box_discovery_telemetry_sample
        elif self.box_discovery_telemetry_policy == "P":
            return self.object_profile.box_discovery_telemetry_sample
        else:
            return 0

    @property
    def periodic_telemetry_sample(self):
        if self.periodic_discovery_telemetry_policy == "E":
            return self.periodic_discovery_telemetry_sample
        elif self.periodic_discovery_telemetry_policy == "P":
            return self.object_profile.periodic_discovery_telemetry_sample
        else:
            return 0

    @property
    def management_vlan(self):
        """
        Return management vlan settings
        :return: Vlan id or None
        """
        if self.segment.management_vlan_policy == "d":
            return None
        elif self.segment.management_vlan_policy == "e":
            return self.segment.management_vlan
        else:
            return self.segment.profile.management_vlan

    @property
    def multicast_vlan(self):
        """
        Return multicast vlan settings
        :return: Vlan id or None
        """
        if self.segment.multicast_vlan_policy == "d":
            return None
        elif self.segment.multicast_vlan_policy == "e":
            return self.segment.multicast_vlan
        else:
            return self.segment.profile.multicast_vlan

    @property
    def escalator_shard(self):
        """
        Returns escalator shard name
        :return:
        """
        if self.tt_system:
            return self.tt_system.shard_name
        else:
            return DEFAULT_TTSYSTEM_SHARD

    @property
    def to_raise_privileges(self):
        if self.cli_privilege_policy == "E":
            return True
        elif self.cli_privilege_policy == "P":
            return self.object_profile.cli_privilege_policy == "E"
        else:
            return False

    def get_autosegmentation_policy(self):
        if self.autosegmentation_policy == "p":
            return self.object_profile.autosegmentation_policy
        else:
            return self.autosegmentation_policy

    @property
    def enable_autosegmentation(self):
        return self.get_autosegmentation_policy() in ("o", "c")

    @property
    def allow_autosegmentation(self):
        return self.get_autosegmentation_policy() == "e"

    def get_access_preference(self):
        if self.access_preference != "P":
            return self.access_preference
        if self.version:
            fw_settings = self.version.get_effective_object_settings()
            return fw_settings.get("access_preference", self.object_profile.access_preference)
        return self.object_profile.access_preference

    def get_event_processing_policy(self):
        if self.event_processing_policy == "P":
            return self.object_profile.event_processing_policy
        else:
            return self.event_processing_policy

    def get_address_resolution_policy(self):
        if self.address_resolution_policy == "P":
            return self.object_profile.address_resolution_policy
        else:
            return self.address_resolution_policy

    def get_denied_firmware_policy(self):
        if self.denied_firmware_policy == "P":
            return self.object_profile.denied_firmware_policy
        return self.denied_firmware_policy

    def get_confdb_raw_policy(self):
        if self.confdb_raw_policy == "P":
            return self.object_profile.confdb_raw_policy
        return self.confdb_raw_policy

    def get_config_policy(self):
        if self.config_policy == "P":
            return self.object_profile.config_policy
        return self.config_policy

    def get_config_fetch_policy(self):
        if self.config_fetch_policy == "P":
            return self.object_profile.config_fetch_policy
        return self.config_fetch_policy

    def get_interface_discovery_policy(self):
        if self.interface_discovery_policy == "P":
            return self.object_profile.interface_discovery_policy
        return self.interface_discovery_policy

    def get_caps_discovery_policy(self):
        if self.caps_discovery_policy == "P":
            return self.object_profile.caps_discovery_policy
        return self.caps_discovery_policy

    def get_vlan_discovery_policy(self):
        if self.vlan_discovery_policy == "P":
            return self.object_profile.vlan_discovery_policy
        return self.vlan_discovery_policy

    def get_effective_box_discovery_running_policy(self):
        if self.box_discovery_running_policy == "P":
            return self.object_profile.box_discovery_running_policy
        return self.box_discovery_running_policy

    def get_effective_periodic_discovery_running_policy(self):
        if self.periodic_discovery_running_policy == "P":
            return self.object_profile.periodic_discovery_running_policy
        return self.periodic_discovery_running_policy

    def get_dynamic_classification_policy(self):
        if self.dynamic_classification_policy == "P":
            return self.object_profile.dynamic_classification_policy
        return self.dynamic_classification_policy

    def get_full_fqdn(self):
        if not self.fqdn:
            return None
        if self.fqdn.endswith(".") or not self.object_profile.fqdn_suffix:
            return self.fqdn[:-1]
        return f"{self.fqdn}.{self.object_profile.fqdn_suffix}"

    def resolve_fqdn(self):
        """
        Resolve FQDN to address
        :return:
        """
        fqdn = self.get_full_fqdn()
        if not fqdn:
            return None
        if self.object_profile.resolver_handler:
            handler = Handler.get_by_id(self.config_diff_filter_handler)
            if handler and handler.allow_resolver:
                return handler.get_handler()(fqdn)
            elif handler and not handler.allow_resolver:
                logger.warning("Handler is not allowed for resolver")
                return None
        import socket

        try:
            return socket.gethostbyname(fqdn)
        except socket.gaierror:
            return None

    @classmethod
    def get_bi_selector(cls, cfg):
        qs = {}
        if "administrative_domain" in cfg:
            d = AdministrativeDomain.get_by_id(cfg["administrative_domain"])
            if d:
                qs["administrative_domain__in"] = d.get_nested()
        if "pool" in cfg:
            qs["pool__in"] = [cfg["pool"]]
        if "profile" in cfg:
            qs["profile__in"] = [cfg["profile"]]
        if "segment" in cfg:
            qs["segment__in"] = [cfg["segment"]]
        if "container" in cfg:
            qs["container__in"] = [cfg["container"]]
        if "vendor" in cfg:
            qs["vendor__in"] = [cfg["vendor"]]
        if "platform" in cfg:
            qs["platform__in"] = [cfg["platform"]]
        if "version" in cfg:
            qs["version__in"] = [cfg["version"]]
        return [int(r) for r in ManagedObject.objects.filter(**qs).values_list("bi_id", flat=True)]

    @property
    def metrics(self):
        metric, last = get_objects_metrics([self])
        return metric.get(self), last.get(self)

    def iter_config_tokens(self, config=None):
        if config is None:
            config = self.config.read()
        if not config:
            return  # no config
        t_name, t_config = self.profile.get_profile().get_config_tokenizer(self)
        if not t_name:
            return  # no tokenizer
        t_cls = tokenizer_loader.get_class(t_name)
        if not t_cls:
            raise ValueError("Invalid tokenizer")
        tokenizer = t_cls(config, **t_config)
        yield from tokenizer

    def iter_normalized_tokens(self, config=None):
        profile = self.profile.get_profile()
        n_handler, n_config = profile.get_config_normalizer(self)
        if not n_handler:
            return
        if not n_handler.startswith("noc."):
            n_handler = "noc.sa.profiles.%s.confdb.normalizer.%s" % (profile.name, n_handler)
        n_cls = get_handler(n_handler)
        if not n_cls:
            return
        normalizer = n_cls(self, self.iter_config_tokens(config), **n_config)
        yield from normalizer

    def get_confdb(self, config=None, cleanup=True):
        """
        Returns ready ConfDB engine instance

        :param config: Configuration data
        :param cleanup: Remove temporary nodes if True
        :return: confdb.Engine instance
        """
        profile = self.profile.get_profile()
        e = Engine()
        # Insert defaults
        defaults = profile.get_confdb_defaults(self)
        if defaults:
            e.insert_bulk(defaults)
        # Get working config
        if config is None:
            config = self.config.read()
        # Insert raw section
        if self.get_confdb_raw_policy() == "E":
            e.insert_bulk(("raw",) + t for t in self.iter_config_tokens(config))
        # Parse and normalize config
        e.insert_bulk(self.iter_normalized_tokens(config))
        # Apply applicators
        for applicator in profile.iter_config_applicators(self, e):
            applicator.apply()
        # Remove temporary nodes
        if cleanup:
            e.cleanup()
        return e

    @property
    def has_confdb_support(self):
        return self.profile.get_profile().has_confdb_support(self)

    @classmethod
    def mock_object(cls, profile=None):
        """
        Return mock object for tests

        :param profile: Profile name
        :return:
        """
        mo = ManagedObject()
        if profile:
            mo.profile = Profile.get_by_name(profile)
        mo.is_mock = True
        return mo

    def iter_scope(self, scope):
        for o in Object.get_managed(self):
            yield from o.iter_scope(scope)

    def get_effective_fm_pool(self):
        if self.fm_pool:
            return self.fm_pool
        return self.pool

    def get_effective_snmp_rate_limit(self) -> int:
        """
        Calculate effective SNMP rate limit
        :return:
        """
        if self.snmp_rate_limit > 0:
            return self.snmp_rate_limit
        if self.version:
            fw_settings = self.version.get_effective_object_settings()
            return fw_settings.get("snmp_rate_limit", self.object_profile.snmp_rate_limit)
        return self.object_profile.snmp_rate_limit

    @classmethod
    def _reset_caches(cls, mo_id: int, credential: bool = False):
        try:
            del cls._id_cache[f"managedobject-id-{mo_id}"]
        except KeyError:
            pass
        try:
            del cls._e_labels_cache[mo_id]
        except KeyError:
            pass
        cache.delete(f"managedobject-id-{mo_id}", version=MANAGEDOBJECT_CACHE_VERSION)
        if credential:
            cache.delete(f"cred-{mo_id}", version=CREDENTIAL_CACHE_VERSION)

    @property
    def events_stream_and_partition(self) -> Tuple[str, int]:
        """
        Return publish stream and partition for events
        :return: stream name, partition
        """
        # @todo: Calculate partition properly
        pool = self.get_effective_fm_pool().name
        return "events.%s" % pool, 0

    @property
    def alarms_stream_and_partition(self) -> Tuple[str, int]:
        """
        Return publish stream and partition for alarms
        :return: stream name, partition
        """
        # @todo: Calculate partition properly
        fm_pool = self.get_effective_fm_pool().name
        stream = f"dispose.{fm_pool}"
        return stream, 0

    @cachetools.cached(_e_labels_cache, key=lambda x: str(x.id), lock=e_labels_lock)
    def get_effective_labels(self) -> List[str]:
        return Label.merge_labels(ManagedObject.iter_effective_labels(self))

    @classmethod
    def iter_effective_labels(cls, instance: "ManagedObject") -> Iterable[List[str]]:
        yield list(instance.labels or [])
        if instance.is_managed:
            yield ["noc::is_managed::="]
        yield list(AdministrativeDomain.iter_lazy_labels(instance.administrative_domain))
        yield list(Pool.iter_lazy_labels(instance.pool))
        yield list(ManagedObjectProfile.iter_lazy_labels(instance.object_profile))
        if instance.effective_service_groups:
            yield ResourceGroup.get_lazy_labels(instance.effective_service_groups)
        yield Label.get_effective_regex_labels("managedobject_name", instance.name)
        lazy_profile_labels = list(Profile.iter_lazy_labels(instance.profile))
        yield Label.ensure_labels(lazy_profile_labels, enable_managedobject=True)
        if instance.vendor:
            lazy_vendor_labels = list(Vendor.iter_lazy_labels(instance.vendor))
            yield Label.ensure_labels(lazy_vendor_labels, enable_managedobject=True)
        if instance.platform:
            lazy_platform_labels = list(Platform.iter_lazy_labels(instance.platform))
            yield Label.ensure_labels(lazy_platform_labels, enable_managedobject=True)
        if instance.address:
            yield Label.get_effective_prefixfilter_labels("managedobject_address", instance.address)
            yield Label.get_effective_regex_labels("managedobject_address", instance.address)
        if instance.description:
            yield Label.get_effective_regex_labels(
                "managedobject_description", instance.description
            )
        if instance.vrf:
            yield list(VRF.iter_lazy_labels(instance.vrf))
        if instance.tt_system:
            yield list(TTSystem.iter_lazy_labels(instance.tt_system))
        if instance.version:
            ep = FirmwarePolicy.get_effective_policies(instance.version, instance.platform)
            if ep:
                yield from [e.effective_labels for e in ep if e.effective_labels]
        if instance.links:
            # If use Link.objects.filter(linked_objects=mo.id).first() - 1.27 ms,
            # Interface = 39.4 µs
            yield ["noc::is_linked::="]
        if instance.diagnostics:
            for d in instance.diagnostics:
                d = instance.get_diagnostic(d)
                yield Label.ensure_labels(
                    [f"funcs::{d.diagnostic}::{d.state}"], enable_managedobject=True
                )

    @classmethod
    def can_set_label(cls, label: str) -> bool:
        return Label.get_effective_setting(label, "enable_managedobject")

    @classmethod
    def uplinks_for_objects(cls, objects: List["ManagedObject"]) -> Dict[int, List[int]]:
        """
        Returns uplinks for list of objects
        :param objects: List of object
        :return: dict of object id -> uplinks
        """
        o = []
        for obj in objects:
            if hasattr(obj, "id"):
                obj = obj.id
            o += [obj]
        uplinks = {obj: [] for obj in o}
        for oid, mo_uplinks in ManagedObject.objects.filter(id__in=o).values_list("id", "uplinks"):
            uplinks[oid] = mo_uplinks or []
        return uplinks

    @classmethod
    def update_uplinks(cls, iter_uplinks: Iterable[ObjectUplinks]) -> None:
        """
        Update ObjectUplinks in database
        :param iter_uplinks: Iterable of ObjectUplinks
        :return:
        """
        from django.db import connection as pg_connection

        obj_data: List[ObjectUplinks] = []
        seen_neighbors: Set[int] = set()
        uplinks: Dict[int, Set[int]] = {}
        for ou in iter_uplinks:
            obj_data += [ou]
            seen_neighbors |= set(ou.rca_neighbors)
            uplinks[ou.object_id] = set(ou.uplinks)
        if not obj_data:
            return  # No uplinks for segment
        # Get downlink_merge window settings
        dlm_settings: Dict[int, int] = {}
        if seen_neighbors:
            with pg_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT mo.id, mop.enable_rca_downlink_merge, mop.rca_downlink_merge_window
                    FROM sa_managedobject mo JOIN sa_managedobjectprofile mop
                        ON mo.object_profile_id = mop.id
                    WHERE mo.id IN %s""",
                    [tuple(seen_neighbors)],
                )
                dlm_settings = {mo_id: dlm_w for mo_id, is_enabled, dlm_w in cursor if is_enabled}
        # Propagate downlink-merge settings downwards
        dlm_windows: Dict[int, int] = {}
        MAX_WINDOW = 1000000
        for o in seen_neighbors:
            ups = uplinks.get(o)
            if not ups:
                continue
            w = min(dlm_settings.get(u, MAX_WINDOW) for u in ups)
            if w == MAX_WINDOW:
                w = 0
            dlm_windows[o] = w
        # Prepare bulk update operation
        for ou in obj_data:
            # mo: "ManagedObject" = ManagedObject.get_by_id(ou.object_id)
            ManagedObject.objects.filter(id=ou.object_id).update(
                uplinks=ou.uplinks,
                rca_neighbors=ou.rca_neighbors,
                dlm_windows=[dlm_windows.get(o, 0) for o in ou.rca_neighbors],
            )
            ManagedObject._reset_caches(ou.object_id)

    @classmethod
    def update_links(cls, linked_objects: List[int], exclude_link_ids: List[str] = None) -> None:
        """

        :param linked_objects:
        :param exclude_link_ids: Exclude link ID from update
        :return:
        """
        from noc.inv.models.link import Link

        coll = Link._get_collection()
        r: Dict[int, Set] = {lo: set() for lo in linked_objects}
        match_expr = {"linked_objects": {"$in": linked_objects}}
        if exclude_link_ids:
            match_expr["_id"] = {"$nin": exclude_link_ids}
        # Check ManagedObject Link Count
        for c in coll.aggregate(
            [
                {"$match": match_expr},
                {"$project": {"neighbors": "$linked_objects", "linked_objects": 1}},
                {"$unwind": "$linked_objects"},
                {"$group": {"_id": "$linked_objects", "neighbors": {"$push": "$neighbors"}}},
            ]
        ):
            if c["_id"] not in r:
                continue
            r[c["_id"]] = set(chain(*c["neighbors"])) - {c["_id"]}
        # Update ManagedObject links
        for lo in r:
            ManagedObject.objects.filter(id=lo).update(links=list(r[lo]))
            ManagedObject._reset_caches(lo)

    @property
    def in_maintenance(self) -> bool:
        """
        Check device is under active maintenance
        :return:
        """
        return any(self.get_active_maintenances())

    def get_active_maintenances(self, timestamp: Optional[datetime.datetime] = None) -> List[str]:
        """
        Getting device active maintenances ids
        :param timestamp:
        :return:
        """
        timestamp = timestamp or datetime.datetime.now()
        r = []
        for mai_id, d in self.affected_maintenances.items():
            if d.get("time_pattern"):
                # Restrict to time pattern
                tp = TimePattern.get_by_id(d["time_pattern"])
                if tp and not tp.match(timestamp):
                    continue
            if datetime.datetime.fromisoformat(d["start"]) > timestamp:
                continue
            if d.get("stop") and datetime.datetime.fromisoformat(d["stop"]) < timestamp:
                # Already complete
                continue
            r.append(mai_id)
        return r

    def get_message_context(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "administrative_domain": {
                "id": str(self.profile.id),
                "name": self.administrative_domain.name,
            },
            "profile": {"id": str(self.profile.id), "name": self.profile.name},
            "object_profile": {"id": str(self.object_profile.id), "name": self.object_profile.name},
        }

    def set_diagnostic_state(
        self,
        diagnostic: str,
        state: bool,
        reason: Optional[str] = None,
        changed_ts: Optional[datetime.datetime] = None,
        data: Optional[Dict[str, Any]] = None,
        bulk: Optional[List[DiagnosticItem]] = None,
    ):
        """
        Set diagnostic ok/fail state
        :param diagnostic: Diagnotic Name
        :param state: True - Enabled; False - Failed
        :param reason: Reason state changed
        :param changed_ts: Timestamp changed
        :param data: Collected checks data
        :param bulk: Return changed diagnostic without saved
        :return:
        """
        state = DIAGNOSTIC_CHECK_STATE[state]
        if diagnostic not in self.diagnostics:
            # logger.info("[%s] Adding diagnostic", dc.diagnostic)
            d = DiagnosticItem(diagnostic=diagnostic)
        else:
            d = self.get_diagnostic(diagnostic)
        if d.state.is_blocked or d.state == state:
            return
        logger.info("[%s] Change diagnostic state: %s -> %s", diagnostic, d.state, state)
        last_state = d.state
        changed = changed_ts or datetime.datetime.now()
        d.state = state
        d.reason = reason
        d.changed = changed.isoformat(sep=" ")
        self.diagnostics[diagnostic] = d.dict()
        if bulk is not None:
            bulk += [d]
        else:
            self.save_diagnostics(self.id, [d])
            self.sync_diagnostic_alarm([d.diagnostic])
            self.register_diagnostic_change(
                d.diagnostic, d.state, from_state=last_state, data=data, reason=reason, ts=changed
            )

    def iter_diagnostic_configs(self) -> Iterable[DiagnosticConfig]:
        """
        Iterate over object diagnostics
        :return:
        """

        if not self.is_managed:
            return
        ac = self.get_access_preference()
        # SNMP Diagnostic
        yield DiagnosticConfig(
            SNMP_DIAG,
            display_description="Check Device response by SNMP request",
            checks=[Check(name="SNMPv1"), Check(name="SNMPv2c")],
            blocked=ac == "C",
            run_policy="F",
            run_order="S",
            discovery_box=True,
            alarm_class="NOC | Managed Object | Access Lost",
            alarm_labels=["noc::access::method::SNMP"],
            reason="Blocked by AccessPreference" if ac == "C" else None,
        )
        yield DiagnosticConfig(
            PROFILE_DIAG,
            display_description="Check device profile",
            show_in_display=False,
            checks=[Check(name="PROFILE")],
            alarm_class="Discovery | Guess | Profile",
            blocked=not self.object_profile.enable_box_discovery_profile,
            run_policy="A",
            run_order="S",
            discovery_box=True,
            reason="Blocked by ObjectProfile AccessPreference"
            if not self.object_profile.enable_box_discovery_profile
            else None,
        )
        # CLI Diagnostic
        yield DiagnosticConfig(
            CLI_DIAG,
            display_description="Check Device response by CLI (TELNET/SSH) request",
            checks=[Check(name="TELNET"), Check(name="SSH")],
            discovery_box=True,
            alarm_class="NOC | Managed Object | Access Lost",
            alarm_labels=["noc::access::method::CLI"],
            blocked=ac == "S" or self.scheme not in {1, 2},
            run_policy="F",
            run_order="S",
            reason="Blocked by AccessPreference"
            if ac == "S" or self.scheme not in {1, 2}
            else None,
        )
        # HTTP Diagnostic
        yield DiagnosticConfig(
            HTTP_DIAG,
            display_description="Check Device response by HTTP/HTTPS request",
            show_in_display=False,
            alarm_class="NOC | Managed Object | Access Lost",
            alarm_labels=["noc::access::method::HTTP"],
            checks=[Check("HTTP"), Check("HTTPS")],
            blocked=False,
            run_policy="D",  # Not supported
            run_order="S",
            reason=None,
        )
        # Access Diagnostic (Blocked - block SNMP & CLI Check ?
        yield DiagnosticConfig(
            "Access",
            dependent=["SNMP", "CLI", "HTTP"],
            show_in_display=False,
            alarm_class="NOC | Managed Object | Access Degraded",
        )
        fm_policy = self.get_effective_fm_pool()
        reason = ""
        if fm_policy == "d":
            reason = "Disable by FM policy"
        elif self.trap_source_type == "d":
            reason = "Disable by source settings"
        # FM
        yield DiagnosticConfig(
            # Reset if change IP/Policy change
            SNMPTRAP_DIAG,
            display_description="Received SNMP Trap from device",
            blocked=self.trap_source_type == "d" or fm_policy == "d",
            run_policy="D",
            reason=reason,
        )
        reason = ""
        if fm_policy == "d":
            reason = "Disable by FM policy"
        elif self.syslog_source_type == "d":
            reason = "Disable by source settings"
        yield DiagnosticConfig(
            # Reset if change IP/Policy change
            SYSLOG_DIAG,
            display_description="Received SYSLOG from device",
            blocked=self.syslog_source_type == "d" or fm_policy == "d",
            run_policy="D",
            reason=reason,
        )
        #
        for dc in ObjectDiagnosticConfig.iter_object_diagnostics(self):
            yield dc

    def update_diagnostics(
        self, checks: List[CheckData] = None, bulk: Optional[List[DiagnosticItem]] = None
    ):
        """
        Update diagnostics by Checks Result ?Source - discovery/manual

        If dependent and checks set -  checks dependent first
        :param checks: List check status
        :param bulk: Return changed diagnostic without saved
        :return:
        """
        now = datetime.datetime.now()
        checks = checks or []
        diagnostics: Dict[str, DiagnosticItem] = {}
        processed = set()
        dependency: List[Tuple[DiagnosticConfig, DiagnosticItem]] = []
        last_state = {}
        # check_result = {c.name: c for c in checks}
        for dc in self.iter_diagnostic_configs():
            # Filter checks
            # dc_checks = [cr for cr in checks if dc.checks and cr.name in dc.checks]
            dc_checks = [
                CheckStatus(
                    name=cr.name, status=cr.status, skipped=cr.skipped, error=cr.error, arg0=cr.arg0
                )
                for cr in checks
                if dc.checks and Check(name=cr.name, arg0=cr.arg0) in dc.checks
            ]
            # Get or Create DiagnosticItem
            if dc.diagnostic not in self.diagnostics:
                # logger.info("[%s] Adding diagnostic", dc.diagnostic)
                d = DiagnosticItem(diagnostic=dc.diagnostic, checks=dc_checks)
            else:
                d = self.get_diagnostic(dc.diagnostic)
            last_state[d.diagnostic] = d.state
            processed.add(dc.diagnostic)
            # Calculate state
            state = None
            if dc.blocked:
                state = DiagnosticState.blocked
            elif dc_checks or dc.dependent:
                check_statuses = [c.status for c in dc_checks if not c.skipped]
                # Check first
                if check_statuses:
                    # ANY or ALL policy apply
                    c_state = (
                        any(check_statuses) if dc.state_policy == "ANY" else all(check_statuses)
                    )
                    state = DIAGNOSTIC_CHECK_STATE[c_state]
                # Defer Dependent
                if dc.dependent:
                    if state:
                        d.state = state
                    dependency.append((dc, d))
                    continue
            else:
                logger.debug("[%s] Not calculate state. Skipping", dc.diagnostic)
                continue
            # Compare state and update
            if not state or d.state == state:
                logger.debug("[%s] State is same", dc.diagnostic)
                continue
            logger.info("[%s] Change diagnostic state: %s -> %s", dc.diagnostic, d.state, state)
            d.state = state
            d.changed = now.replace(microsecond=0).isoformat(sep=" ")
            d.checks = dc_checks
            diagnostics[dc.diagnostic] = d
        # Remove
        removed: List[str] = []
        for d in set(self.diagnostics) - set(processed):
            del self.diagnostics[d]
            removed += [d]
        # Calculate State for defer Dependent
        for dc, d in dependency:
            d_states = [d.state]
            # Dependency states
            for dd in dc.dependent:
                if dd in diagnostics:
                    dd = diagnostics[dd]
                elif dd in self.diagnostics:
                    dd = self.get_diagnostic(dd)
                else:
                    logger.warning("[%s] Unknown dependency: %s", dc.diagnostic, dd)
                    continue
                if dd.state.is_blocked:
                    # Skipping ?
                    continue
                d_states.append(dd.state)
            # Calculate State
            state = DiagnosticState.enabled
            if DiagnosticState.enabled not in d_states and DiagnosticState.failed not in d_states:
                state = DiagnosticState.unknown
            elif dc.state_policy == "ANY" and DiagnosticState.enabled not in d_states:
                state = DiagnosticState.failed
            elif dc.state_policy == "ALL" and DiagnosticState.failed in d_states:
                state = DiagnosticState.failed
            if state == DiagnosticState.unknown and dc.diagnostic in self.diagnostics:
                # Unknown state, Remove
                removed += [dc.diagnostic]
                del self.diagnostics[dc.diagnostic]
                continue
            elif state != d.state:
                logger.info(
                    "[%s] Change complex diagnostic state: %s -> %s", dc.diagnostic, d.state, state
                )
                d.state = state
                d.changed = now.replace(microsecond=0).isoformat(sep=" ")
                diagnostics[dc.diagnostic] = d
        # Update
        if not diagnostics and not removed:
            return
        self.diagnostics.update({d: dd.dict() for d, dd in diagnostics.items()})
        if bulk is not None:
            bulk += list(diagnostics.values())
        else:
            self.save_diagnostics(self.id, list(diagnostics.values()), removed)
            self.sync_diagnostic_alarm(list(diagnostics))
            # Register changed message
            for di in diagnostics.values():
                self.register_diagnostic_change(
                    di.diagnostic,
                    state=di.state,
                    from_state=last_state.get(di.diagnostic, DiagnosticState.unknown),
                    reason=di.reason,
                    ts=di.changed,
                )

    @classmethod
    def save_diagnostics(
        cls,
        mo_id: int,
        diagnostics: Optional[List[DiagnosticItem]] = None,
        removed: Optional[List[str]] = None,
    ):
        """
        Update diagnostic on database
        :param mo_id: ManagedObject id
        :param diagnostics: List diagnostics Item for save
        :param removed: List diagnostic name for remove
        :return:
        """
        from django.db import connection as pg_connection

        # @todo effective labels
        if not diagnostics and not removed:
            return
        with pg_connection.cursor() as cursor:
            if diagnostics:
                logger.debug("[%s] Saving changes", list(diagnostics))
                cursor.execute(
                    """
                     UPDATE sa_managedobject
                     SET diagnostics = diagnostics || %s::jsonb
                     WHERE id = %s""",
                    [
                        orjson.dumps(
                            {d.diagnostic: d for d in diagnostics}, default=default
                        ).decode("utf-8"),
                        mo_id,
                    ],
                )
            if removed:
                logger.debug("[%s] Removed diagnostics", list(removed))
                cursor.execute(
                    f"""
                     UPDATE sa_managedobject
                     SET diagnostics = diagnostics {" #- %s " * len(removed)}
                     WHERE id = %s""",
                    ["{%s}" % r for r in removed] + [mo_id],
                )
        cls._reset_caches(mo_id)

    def get_diagnostic(self, diagnostic) -> Optional[DiagnosticItem]:
        if diagnostic not in self.diagnostics:
            return
        if isinstance(self.diagnostics[diagnostic], DiagnosticItem):
            return self.diagnostics[diagnostic]
        return DiagnosticItem.parse_obj(self.diagnostics[diagnostic])

    def reset_diagnostic(self, diagnostics: List[str]):
        """

        :param diagnostics:
        :return:
        """
        from django.db import connection as pg_connection

        removed = []
        ts = datetime.datetime.now()
        for d in diagnostics:
            if d in self.diagnostics:
                d = self.get_diagnostic(d)
                self.register_diagnostic_change(
                    d.diagnostic, state=DiagnosticState.unknown, from_state=d.state, ts=ts
                )
                removed.append(d.diagnostic)
        # If Failed state - clear alarm
        if not removed:
            return
        logger.debug("[%s] Removed diagnostics", ";".join(removed))
        self.sync_diagnostic_alarm(removed)
        with pg_connection.cursor() as cursor:
            cursor.execute(
                f"""
                 UPDATE sa_managedobject
                 SET diagnostics = diagnostics {" #- %s " * len(removed)}
                 WHERE id = %s""",
                ["{%s}" % r for r in removed] + [self.id],
            )
        for d in removed:
            # Do after sync-alarm and register_changed
            del self.diagnostics[d]
        self._reset_caches(self.id)

    def sync_diagnostic_alarm(self, diagnostics: Optional[List[str]] = None):
        """
        Raise & clear Alarm for diagnostic. Only diagnostics with alarm_class set will be synced.
        If diagnostics param is set and alarm_class is not set - clear alarm
         For dependent - Group alarm base on diagnostic with alarm for depended
        :param diagnostics: If set - sync only params diagnostic and depends
        :return:
        """
        from noc.core.service.loader import get_service

        now = datetime.datetime.now()
        # Group Alarms
        groups = {}
        #
        alarms = {}
        alarm_config: Dict[str, Dict[str, Any]] = {}  # diagnostic -> AlarmClass Map
        messages: List[Dict[str, Any]] = []  # Messages for send dispose
        processed = set()
        diagnostics = set(diagnostics or [])
        for dc in self.iter_diagnostic_configs():
            if not dc.alarm_class:
                continue
            alarm_config[dc.diagnostic] = {
                "alarm_class": dc.alarm_class,
                "alarm_labels": dc.alarm_labels or [],
            }
            if dc.diagnostic in processed:
                continue
            if diagnostics and not dc.dependent and dc.diagnostic not in diagnostics:
                # Skip non-changed diagnostics
                continue
            if diagnostics and dc.dependent and not diagnostics.intersection(set(dc.dependent)):
                # Skip non-affected depended diagnostics
                continue
            d = self.get_diagnostic(dc.diagnostic)
            if dc.dependent:
                groups[dc.diagnostic] = []
                for d_name in dc.dependent:
                    dd = self.get_diagnostic(d_name)
                    if dd and dd.state == DiagnosticState.failed:
                        groups[dc.diagnostic] += [{"diagnostic": d_name, "reason": dd.reason or ""}]
                    processed.add(d_name)
            elif d and d.state == d.state.failed:
                alarms[dc.diagnostic] = {
                    "timestamp": now,
                    "reference": f"dc:{self.id}:{d.diagnostic}",
                    "managed_object": self.id,
                    "$op": "raise",
                    "alarm_class": dc.alarm_class,
                    "labels": dc.alarm_labels or [],
                    "vars": {"reason": d.reason or ""},
                }
            else:
                alarms[dc.diagnostic] = {
                    "timestamp": now,
                    "reference": f"dc:{self.id}:{dc.diagnostic}",
                    "$op": "clear",
                }
        # Group Alarm
        for d in groups:
            messages += [
                {
                    "$op": "ensure_group",
                    "reference": f"dc:{d}:{self.id}",
                    "alarm_class": alarm_config[d]["alarm_class"],
                    "alarms": [
                        {
                            "reference": f'dc:{dd["diagnostic"]}:{self.id}',
                            "alarm_class": alarm_config[dd["diagnostic"]]["alarm_class"],
                            "managed_object": self.id,
                            "timestamp": now,
                            "labels": alarm_config[dd["diagnostic"]]["alarm_labels"],
                            "vars": {"reason": dd["reason"] or ""},
                        }
                        for dd in groups[d]
                    ],
                }
            ]
        # Other
        for d in alarms:
            if d in processed:
                continue
            messages += [alarms[d]]
        # Send Dispose
        svc = get_service()
        for msg in messages:
            stream, partition = self.alarms_stream_and_partition
            svc.publish(
                orjson.dumps(msg),
                stream=stream,
                partition=partition,
            )
            logger.debug(
                "Dispose: %s", orjson.dumps(msg, option=orjson.OPT_INDENT_2).decode("utf-8")
            )

    def register_diagnostic_change(
        self,
        diagnostic: str,
        state: str,
        from_state: str = DiagnosticState.unknown,
        reason: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ts: Optional[datetime.datetime] = None,
    ):
        """
        Save diagnostic state changes to Archive.
        1. Send data to BI Model
        2. Register MX Message
        3. Register object notification
        :param diagnostic: - Diagnostic name
        :param state: Current state
        :param from_state: Previous State
        :param data: Checked data
        :param reason:
        :param ts:
        :return:
        """
        from noc.core.service.loader import get_service

        svc = get_service()
        if isinstance(ts, str):
            ts = datetime.datetime.fromisoformat(ts)
        now = ts or datetime.datetime.now()
        # Send Data
        dd = {
            "date": now.date().isoformat(),
            "ts": now.replace(microsecond=0).isoformat(sep=" "),
            "managed_object": self.bi_id,
            "diagnostic_name": diagnostic,
            "state": state,
            "from_state": from_state,
        }
        if reason:
            dd["reason"] = reason
        if data:
            dd["data"] = orjson.dumps(data).decode(DEFAULT_ENCODING)
        svc.register_metrics("diagnostichistory", [dd], key=self.bi_id)
        # Send Stream
        # ? always send (from policy)
        if config.message.enable_diagnostic_change:
            send_message(
                data={
                    "name": diagnostic,
                    "state": state,
                    "from_state": from_state,
                    "reason": reason,
                    "managed_object": self.get_message_context(),
                },
                message_type="diagnostic_change",
                headers={
                    MX_LABELS: MX_H_VALUE_SPLITTER.join(self.effective_labels).encode(
                        encoding=DEFAULT_ENCODING
                    ),
                },
            )
        # Send Notification

    def update_init(self):
        """
        Update initial_data field
        :return:
        """
        self.initial_data = _get_field_snapshot(self.__class__, self)

    def iter_collected_metrics(
        self, is_box: bool = False, is_periodic: bool = True
    ) -> Iterable[MetricCollectorConfig]:
        """
        Return metrics setting for colleted by box or periodic
        :param is_box:
        :param is_periodic:
        :return:
        """
        if not self.is_managed:
            return
        from noc.inv.models.interface import Interface
        from noc.inv.models.subinterface import SubInterface
        from noc.inv.models.interfaceprofile import InterfaceProfile

        metrics: List[MetricItem] = []
        for mc in ManagedObjectProfile.get_object_profile_metrics(self.object_profile.id).values():
            if (is_box and not mc.enable_box) or (is_periodic and not mc.enable_periodic):
                continue
            metrics.append(
                MetricItem(
                    name=mc.metric_type.name,
                    field_name=mc.metric_type.field_name,
                    scope_name=mc.metric_type.scope.table_name,
                    is_stored=mc.is_stored,
                    is_compose=mc.metric_type.is_compose,
                )
            )
        if metrics:
            logger.debug("Object metrics: %s", ",".join(m.name for m in metrics))
            yield MetricCollectorConfig(collector="managed_object", metrics=tuple(metrics))
        for i in (
            Interface._get_collection()
            .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
            .find(
                {"managed_object": self.id, "type": "physical"},
                {
                    "_id": 1,
                    "name": 1,
                    "admin_status": 1,
                    "oper_status": 1,
                    "ifindex": 1,
                    "profile": 1,
                    "service": 1,
                },
            )
        ):
            i_profile = InterfaceProfile.get_by_id(i["profile"])
            logger.debug("Interface %s. ipr=%s", i["name"], i_profile)
            if not i_profile:
                continue  # No metrics configured
            metrics: List[MetricItem] = []
            for mc in i_profile.metrics:
                if (is_box and not mc.enable_box) or (is_periodic and not mc.enable_periodic):
                    continue
                # Check metric collected policy
                if not i_profile.allow_collected_metric(
                    i.get("admin_status"), i.get("oper_status"), mc.metric_type.name
                ):
                    continue
                mi = MetricItem(
                    name=mc.metric_type.name,
                    field_name=mc.metric_type.field_name,
                    scope_name=mc.metric_type.scope.table_name,
                    is_stored=mc.is_stored,
                    is_compose=mc.metric_type.is_compose,
                )
                if mi not in metrics:
                    metrics.append(mi)
                # Append Compose metrics for collect
                if mc.metric_type.is_compose:
                    for mt in mc.metric_type.compose_inputs:
                        mi = MetricItem(
                            name=mt.name,
                            field_name=mt.field_name,
                            scope_name=mc.metric_type.scope.table_name,
                            is_stored=True,
                            is_compose=False,
                        )
                        if mi not in metrics:
                            metrics.append(mi)
            if not metrics:
                continue
            ifindex = i.get("ifindex")
            yield MetricCollectorConfig(
                collector="managed_object",
                metrics=tuple(metrics),
                labels=(f"noc::interface::{i['name']}",),
                hints=[f"ifindex::{ifindex}"] if ifindex else None,
                # service=i.get("service"),
            )
            if not i_profile.allow_subinterface_metrics:
                continue
            for si in (
                SubInterface._get_collection()
                .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
                .find({"interface": i["_id"]}, {"name": 1, "interface": 1, "ifindex": 1})
            ):
                ifindex = si.get("ifindex")
                yield MetricCollectorConfig(
                    collector="managed_object",
                    metrics=tuple(metrics),
                    labels=(
                        f"noc::interface::{i['name']}",
                        f"noc::subinterface::{si['name']}",
                    ),
                    hints=[f"ifindex::{ifindex}"] if ifindex else None,
                )

    @classmethod
    def get_metric_config(cls, mo: "ManagedObject"):
        """
        Return MetricConfig for Metrics service
        :param mo:
        :return:
        """
        from noc.inv.models.interface import Interface
        from noc.inv.models.interfaceprofile import InterfaceProfile

        if not mo.is_managed:
            return {}
        icoll = Interface._get_collection()
        s_metrics = mo.object_profile.get_object_profile_metrics(mo.object_profile.id)
        labels = []
        for ll in sorted(mo.effective_labels):
            l_c = Label.get_by_name(ll)
            labels.append({"label": ll, "expose_metric": l_c.expose_metric if l_c else False})
        items = []
        for iface in icoll.find(
            {"managed_object": mo.id}, {"name", "effective_labels", "profile"}
        ).sort([("name", ASCENDING)]):
            ip = InterfaceProfile.get_by_id(iface["profile"])
            metrics = [
                {
                    "name": mc.metric_type.field_name,
                    "is_stored": mc.is_stored,
                    "is_composed": bool(mc.metric_type.compose_expression),
                }
                for mc in ip.metrics
            ]
            if not metrics:
                continue
            items.append(
                {
                    "key_labels": [f"noc::interface::{iface['name']}"],
                    "labels": [
                        {"label": ll, "expose_metric": False}
                        for ll in sorted(iface.get("effective_labels", []))
                    ],
                    "metrics": metrics,
                }
            )
        return {
            "type": "managed_object",
            "bi_id": mo.bi_id,
            "fm_pool": mo.get_effective_fm_pool().name,
            "labels": labels,
            "metrics": [
                {
                    "name": mc.metric_type.field_name,
                    "is_stored": mc.is_stored,
                    "is_composed": bool(mc.metric_type.compose_expression),
                }
                for mc in s_metrics.values()
            ],
            "items": items,
        }

    @property
    def has_configured_metrics(self) -> bool:
        """
        Check configured collected metrics
        :return:
        """
        from noc.sla.models.slaprobe import SLAProbe
        from noc.inv.models.sensor import Sensor
        from noc.inv.models.object import Object
        from mongoengine.queryset import Q as m_Q

        if not self.is_managed:
            return False
        sla_probe = SLAProbe.objects.filter(managed_object=self.id).first()
        o = Object.get_managed(self)
        sensor = Sensor.objects.filter(m_Q(managed_object=self.id) | m_Q(object__in=o)).first()
        config = self.get_metric_config(self)
        return bool(sla_probe or sensor or config.get("metrics") or config.get("items"))


@on_save
class ManagedObjectAttribute(NOCModel):
    class Meta(object):
        verbose_name = "Managed Object Attribute"
        verbose_name_plural = "Managed Object Attributes"
        db_table = "sa_managedobjectattribute"
        app_label = "sa"
        unique_together = [("managed_object", "key")]
        ordering = ["managed_object", "key"]

    managed_object = ForeignKey(ManagedObject, verbose_name="Managed Object", on_delete=CASCADE)
    key = CharField("Key", max_length=64)
    value = CharField("Value", max_length=4096, blank=True, null=True)

    def __str__(self):
        return "%s: %s" % (self.managed_object, self.key)

    def on_save(self):
        cache.delete(f"cred-{self.managed_object.id}", version=CREDENTIAL_CACHE_VERSION)


# object.scripts. ...
class ScriptsProxy(object):
    def __init__(self, obj, caller=None):
        self._object = obj
        self._cache = {}
        self._caller = caller or ScriptCaller

    def __getattr__(self, name):
        if name in self._cache:
            return self._cache[name]
        if not script_loader.has_script("%s.%s" % (self._object.profile.name, name)):
            raise AttributeError("Invalid script %s" % name)
        cw = self._caller(self._object, name)
        self._cache[name] = cw
        return cw

    def __getitem__(self, item):
        return getattr(self, item)

    def __contains__(self, item):
        """
        Check object has script name
        """
        if "." not in item:
            # Normalize to full name
            item = "%s.%s" % (self._object.profile.name, item)
        return script_loader.has_script(item)

    def __iter__(self):
        prefix = self._object.profile.name + "."
        return (x.split(".")[-1] for x in script_loader.iter_scripts() if x.startswith(prefix))


class ActionsProxy(object):
    class CallWrapper(object):
        def __init__(self, obj, name, action):
            self.name = name
            self.object = obj
            self.action = action

        def __call__(self, **kwargs):
            return self.action.execute(self.object, **kwargs)

    def __init__(self, obj):
        self._object = obj
        self._cache = {}

    def __getattr__(self, name):
        if name in self._cache:
            return self._cache[name]
        a = Action.objects.filter(name=name).first()
        if not a:
            raise AttributeError(name)
        cw = ActionsProxy.CallWrapper(self._object, name, a)
        self._cache[name] = cw
        return cw


class MatchersProxy(object):
    def __init__(self, obj):
        self._object = obj
        self._data = None

    def _rebuild(self):
        # Build version structure
        version = {}
        if self._object.vendor:
            version["verndor"] = self._object.vendor.code
        if self._object.platform:
            version["platform"] = self._object.platform.name
        if self._object.version:
            version["version"] = self._object.version.version
        if self._object.software_image:
            version["image"] = self._object.software_image
        # Compile matchers
        matchers = self._object.get_profile().matchers
        self._data = {m: match(version, matchers[m]) for m in matchers}

    def __getattr__(self, name):
        if self._data is None:
            # Rebuild matchers
            self._rebuild()
        return self._data[name]

    def __contains__(self, item):
        if self._data is None:
            self._rebuild()
        return item in self._data


# Avoid circular references
from .useraccess import UserAccess
from .groupaccess import GroupAccess
from .action import Action
from noc.core.pm.utils import get_objects_metrics
from noc.ip.models.vrf import VRF

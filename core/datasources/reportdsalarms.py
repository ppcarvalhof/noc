# ----------------------------------------------------------------------
# ReportDsAlarms datasource
# ----------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import List, Iterable, Dict, Any, Optional
import datetime
import operator

# Third-party modules
import bson
import pandas as pd
import cachetools
from pymongo import ReadPreference


# NOC modules
from .base import BaseDataSource, FieldInfo
from noc.fm.models.activealarm import ActiveAlarm
from noc.fm.models.alarmclass import AlarmClass
from noc.fm.models.archivedalarm import ArchivedAlarm
from noc.sa.models.managedobject import ManagedObject
from noc.sa.models.profile import Profile
from noc.inv.models.platform import Platform
from noc.inv.models.firmware import Firmware
from noc.inv.models.resourcegroup import ResourceGroup
from noc.inv.models.discoveryid import DiscoveryID
from noc.inv.models.object import Object
from noc.inv.models.networksegment import NetworkSegment
from noc.project.models.project import Project
from noc.crm.models.subscriberprofile import SubscriberProfile
from noc.services.web.apps.fm.alarm.views import AlarmApplication


class ReportDsAlarms(BaseDataSource):
    name = "reportdsalarms"
    index_field = "alarm_id"

    SEGMENT_PATH_DEPTH = 7
    CONTAINER_PATH_DEPTH = 7

    fields: List[FieldInfo] = (
        [
            FieldInfo(
                name="alarm_id",
                # label="Alarm Id",
                description="Идентификатор аварии",
            ),
            FieldInfo(
                name="root_id",
                # label="Alarm Root",
                description="Первопричина",
            ),
            FieldInfo(
                name="from_ts",
                # label="FROM_TS",
                description="Время начала",
            ),
            FieldInfo(
                name="to_ts",
                # label="TO_TS",
                description="Время окончания",
            ),
            FieldInfo(
                name="duration_sec",
                # label="DURATION_SEC",
                description="Продолжительность (сек)",
                type="int",
            ),
            FieldInfo(
                name="object_name",
                # label="OBJECT_NAME",
                description="Имя устройства",
            ),
            FieldInfo(
                name="object_address",
                # label="OBJECT_ADDRESS",
                description="IP Адрес",
            ),
            FieldInfo(
                name="object_hostname",
                # label="OBJECT_HOSTNAME",
                description="Hostname устройства",
            ),
            FieldInfo(
                name="object_profile",
                # label="OBJECT_PROFILE",
                description="Профиль",
            ),
            FieldInfo(
                name="object_object_profile",
                # label="OBJECT_OBJECT_PROFILE",
                description="Профиль объекта",
            ),
            FieldInfo(
                name="object_admdomain",
                # label="OBJECT_ADMDOMAIN",
                description="Зона ответственности",
            ),
            FieldInfo(
                name="object_platform",
                # label="OBJECT_PLATFORM",
                description="Платформа",
            ),
            FieldInfo(
                name="object_version",
                # label="OBJECT_VERSION",
                description="Версия",
            ),
            FieldInfo(
                name="object_project",
                # label="OBJECT_PROJECT",
                description="Проект",
            ),
            FieldInfo(
                name="alarm_class",
                # label="ALARM_CLASS",
                description="Класс аварии",
            ),
            FieldInfo(
                name="alarm_subject",
                # label="ALARM_SUBJECT",
                description="Тема",
            ),
            FieldInfo(
                name="maintenance",
                # label="MAINTENANCE",
                description="Активный РНР",
            ),
            FieldInfo(
                name="objects",
                # label="OBJECTS",
                description="Число задетых устройства",
                type="int",
            ),
            FieldInfo(
                name="subscribers",
                # label="SUBSCRIBERS",
                description="Абоненты",
                type="int",
            ),
            FieldInfo(
                name="tt",
                # label="TT",
                description="Номер ТТ",
            ),
            FieldInfo(
                name="escalation_ts",
                # label="ESCALATION_TS",
                description="Время эскалации",
            ),
            FieldInfo(
                name="location",
                # label="LOCATION",
                description="Месторасположение",
            ),
        ]
        + [
            FieldInfo(name=f"subsprof_{sp.name}")  # label=sp.name.upper())
            for sp in SubscriberProfile.objects.filter(show_in_summary=True).order_by("name")
        ]
        + [
            FieldInfo(
                name=f"container_{i}",
                # label=f"CONTAINER_{i}",
                description=f"Контейнер (Уровень {i + 1})",
            )
            for i in range(CONTAINER_PATH_DEPTH)
        ]
        + [
            FieldInfo(
                name=f"segment_{i}",  # label=f"SEGMENT_{i}",
                description=f"Сегмент (Уровень {i + 1})",
            )
            for i in range(SEGMENT_PATH_DEPTH)
        ]
    )

    _object_location_cache = cachetools.TTLCache(maxsize=1000, ttl=600)

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_object_location_cache"))
    def get_object_location(cls, oid: str) -> str:
        loc = AlarmApplication(None)
        return ", ".join(loc.location(oid))

    @classmethod
    def _clear_caches(cls):
        cls._object_location_cache.clear()
        Object._id_cache.clear()
        Platform._id_cache.clear()
        Profile._id_cache.clear()
        Firmware._id_cache.clear()
        AlarmClass._id_cache.clear()

    @classmethod
    async def query(cls, fields: Optional[Iterable[str]] = None, *args, **kwargs) -> pd.DataFrame:
        data = [mm async for mm in cls.iter_query(fields or [], *args, **kwargs)]
        df = pd.DataFrame.from_records(
            data,
            index=cls.index_field,
            columns=[cls.index_field]
            + [
                ff.name
                for ff in cls.fields
                if not fields or (ff.name in fields and ff.name != cls.index_field)
            ],
        )
        # for ff in cls.fields:
        #     if not fields or ff.name in fields or ff.name == cls.index_field:
        #         continue
        #     if ff.name in df.columns:
        #         df.drop(ff.name, axis=1)
        return df

    @classmethod
    def items_to_dict(cls, items):
        """
        Convert a list of summary items to dict profile -> summary
        """
        return {r["profile"]: r["summary"] for r in items}

    @classmethod
    def iter_data(cls, start, end, **filters: Optional[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        # print("Iter Data", start, end, filters)
        if "objectids" in filters:
            match = {"_id": {"$in": [bson.ObjectId(x) for x in filters["objectids"]]}}
        else:
            match = {"timestamp": {"$gte": start, "$lte": end}}
        match_duration, mos_filter, ex_resource_group = {}, {}, None
        datenow = datetime.datetime.now()
        alarm_collections = []

        for name in filters:
            # name, values = ff["name"], ff["values"]
            values = filters[name]
            if name == "source":
                if "active" in values or "both" in values:
                    alarm_collections += [ActiveAlarm]
                if "archive" in values or "both" in values:
                    alarm_collections += [ArchivedAlarm]
            elif name == "min_subscribers":
                match_duration["total_subscribers_sum.sum"] = {"$gte": int(values[0])}
            elif name == "min_objects":
                match_duration["total_objects_sum.sum"] = {"$gte": int(values[0])}
            elif name == "min_duration":
                match_duration["duration"] = {"$gte": int(values[0])}
            elif name == "max_duration":
                if "duration" in match_duration:
                    match_duration["duration"]["$lte"] = int(values[0])
                else:
                    match_duration["duration"] = {"$lte": int(values[0])}
            elif name == "alarm_class":
                match["alarm_class"] = bson.ObjectId(values[0])
            elif name == "adm_path":
                match["adm_path"] = {"$in": values}
                mos_filter["administrative_domain__in"] = values
            elif name == "segment":
                match["segment_path"] = bson.ObjectId(values[0])
            elif name == "resource_group":
                resource_group = ResourceGroup.get_by_id(values[0])
                mos_filter["effective_service_groups__overlap"] = ResourceGroup.get_nested_ids(
                    resource_group
                )
            if name == "ex_resource_group":
                ex_resource_group = ResourceGroup.get_by_id(values[0])

        if mos_filter:
            mos = ManagedObject.objects.filter(is_managed=True).filter(**mos_filter)
            if ex_resource_group:
                mos = mos.exclude(
                    effective_service_groups__overlap=ResourceGroup.get_nested_ids(
                        ex_resource_group
                    )
                )
            match["managed_object"] = {"$in": list(mos.values_list("id", flat=True))}
        for coll in alarm_collections:
            # if isinstance(coll, ActiveAlarm):
            pipeline = []
            if match:
                pipeline += [{"$match": match}]
            pipeline += [
                # {
                #     "$lookup": {
                #         "from": "noc.objects",
                #         "localField": "container_path",
                #         "foreignField": "_id",
                #         "as": "container_path_l",
                #     }
                # },
                # {
                #     "$lookup": {
                #         "from": "noc.networksegments",
                #         "localField": "segment_path",
                #         "foreignField": "_id",
                #         "as": "segment_path_l",
                #     }
                # },
                {
                    "$addFields": {
                        "duration": {
                            "$divide": [
                                {
                                    "$subtract": [
                                        "$clear_timestamp" if coll is ArchivedAlarm else datenow,
                                        "$timestamp",
                                    ]
                                },
                                1000,
                            ]
                        },
                        "total_objects_sum": {
                            "$reduce": {
                                "input": "$total_objects",
                                "initialValue": {"sum": 0},
                                "in": {"sum": {"$add": ["$$value.sum", "$$this.summary"]}},
                            }
                        },
                        "total_subscribers_sum": {
                            "$reduce": {
                                "input": "$total_subscribers",
                                "initialValue": {"sum": 0},
                                "in": {"sum": {"$add": ["$$value.sum", "$$this.summary"]}},
                            }
                        },
                        # "container_path_l": {
                        #     "$map": {"input": "$container_path_l", "as": "cc", "in": "$$cc.name"}
                        # },
                        "container_path_l": [],
                        # "segment_path_l": {
                        #     "$map": {"input": "$segment_path_l", "as": "ns", "in": "$$ns.name"}
                        # },
                    }
                },
            ]
            if match_duration:
                pipeline += [{"$match": match_duration}]

            # print(pipeline, alarm_collections)
            for row in (
                coll._get_collection()
                .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
                .aggregate(pipeline)
            ):
                yield row

    @classmethod
    async def iter_query(
        cls, fields: Optional[Iterable[str]] = None, *args, **kwargs
    ) -> Iterable[Dict[str, Any]]:
        if "start" not in kwargs:
            raise ValueError("Start filter is required")
        moss = {
            mo["id"]: mo
            for mo in ManagedObject.objects.filter().values(
                "id",
                "name",
                "address",
                "profile",
                "object_profile__name",
                "administrative_domain__name",
                "platform",
                "version",
                "project",
            )
        }
        fields = fields or []
        mo_hostname = {}
        if not fields or "object_hostname" in fields:
            mo_hostname = {
                val["object"]: val["hostname"]
                for val in DiscoveryID._get_collection()
                .with_options(read_preference=ReadPreference.SECONDARY_PREFERRED)
                .find({"hostname": {"$exists": 1}}, {"object": 1, "hostname": 1})
            }
        maintenance = {}
        # if "maintenance" in fields:
        #     maintenance = Maintenance.currently_affected()
        container_path_fields = [field for field in fields if field.startswith("container_")]
        segment_path_fields = [field for field in fields if field.startswith("segment_")]
        subscribers_profile = []
        if not fields or "subscribers" in fields:
            subscribers_profile = [
                sp
                for sp in SubscriberProfile.objects.filter(show_in_summary=True)
                .values_list("name", "id")
                .order_by("name")
            ]
        for aa in cls.iter_data(**kwargs):
            mo = moss[aa["managed_object"]]
            loc = ""
            if (not fields or "location" in fields) and aa.get("container_path"):
                loc = cls.get_object_location(aa["container_path"][-1])
            platform, version, project = None, None, None
            if mo["platform"]:
                platform = Platform.get_by_id(mo["platform"]).name
            if mo["project"]:
                project = Project.get_by_id(mo["project"]).name
            if mo["version"]:
                version = Firmware.get_by_id(mo["version"]).version
            r = {
                "alarm_id": str(aa["_id"]),
                "root_id": str(aa["root"]) if aa.get("root") else "",
                "from_ts": aa["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "to_ts": aa["clear_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                if "clear_timestamp" in aa
                else "",
                "duration_sec": round(aa["duration"]),
                "object_name": mo["name"],
                "object_address": mo["address"],
                "object_hostname": mo_hostname.get(aa["managed_object"], ""),
                "object_profile": Profile.get_by_id(mo["profile"]).name,
                "object_object_profile": mo["object_profile__name"],
                "object_admdomain": mo["administrative_domain__name"],
                "object_platform": platform,
                "object_version": version,
                "object_project": project,
                "alarm_class": AlarmClass.get_by_id(aa["alarm_class"]).name,
                "alarm_subject": "",
                "objects": aa["total_objects_sum"]["sum"],
                "subscribers": aa["total_subscribers_sum"]["sum"],
                "tt": aa.get("escalation_tt"),
                "escalation_ts": aa["escalation_ts"].strftime("%Y-%m-%d %H:%M:%S")
                if "escalation_ts" in aa
                else "",
                "location": loc,
                "maintenance": "Yes"
                if "clear_timestamp" not in aa and aa["managed_object"] in maintenance
                else "No",
            }
            for sp_name, sp_id in subscribers_profile:
                dd = cls.items_to_dict(aa["total_subscribers"])
                r[f"subsprof_{sp_name}"] = dd.get(sp_id, "")

            for field in container_path_fields:
                _, index = field.split("_")
                v, index = "", int(index)
                if index < len(aa["container_path"]):
                    o = Object.get_by_id(aa["container_path"][index])
                    if o:
                        v = o.name
                r[field] = v

            for field in segment_path_fields:
                _, index = field.split("_")
                v, index = "", int(index)
                if index < len(aa["segment_path"]):
                    o = NetworkSegment.get_by_id(aa["segment_path"][index])
                    if o:
                        v = o.name
                r[field] = v

            yield r
        cls._clear_caches()

# ---------------------------------------------------------------------
# NotificationGroup model
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import datetime
import logging
import operator
from threading import Lock

# Third-party modules
from django.db import models
import cachetools

# NOC modules
from noc.core.model.base import NOCModel
from noc.aaa.models.user import User
from noc.settings import LANGUAGE_CODE
from noc.core.timepattern import TimePatternList
from noc.core.service.pub import pub
from noc.core.model.decorator import on_delete_check
from .timepattern import TimePattern

id_lock = Lock()
logger = logging.getLogger(__name__)


NOTIFICATION_TOPICS = {"mail": "mailsender", "tg": "tgsender", "icq": "icqsender"}

NOTIFICATION_METHOD_CHOICES = [(x, x) for x in sorted(NOTIFICATION_TOPICS)]
USER_NOTIFICATION_METHOD_CHOICES = NOTIFICATION_METHOD_CHOICES


@on_delete_check(
    check=[
        ("cm.ObjectNotify", "notification_group"),
        ("dns.DNSZone", "notification_group"),
        ("dns.DNSZoneProfile", "notification_group"),
        ("fm.ActiveAlarm", "clear_notification_group"),
        ("fm.AlarmTrigger", "notification_group"),
        ("fm.EventTrigger", "notification_group"),
        ("inv.InterfaceProfile", "status_change_notification"),
        ("main.ReportSubscription", "notification_group"),
        ("main.NotificationGroupOther", "notification_group"),
        ("main.NotificationGroupUser", "notification_group"),
        ("main.SystemNotification", "notification_group"),
        ("sa.ObjectNotification", "notification_group"),
        ("vc.VCDomainProvisioningConfig", "notification_group"),
        ("peer.PeeringPoint", "prefix_list_notification_group"),
    ]
)
class NotificationGroup(NOCModel):
    """
    Notification Groups
    """

    class Meta(object):
        verbose_name = "Notification Group"
        verbose_name_plural = "Notification Groups"
        app_label = "main"
        db_table = "main_notificationgroup"
        ordering = ["name"]

    name = models.CharField("Name", max_length=64, unique=True)
    description = models.TextField("Description", null=True, blank=True)

    _id_cache = cachetools.TTLCache(maxsize=100, ttl=60)
    _name_cache = cachetools.TTLCache(maxsize=100, ttl=60)

    def __str__(self):
        return self.name

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_id_cache"), lock=lambda _: id_lock)
    def get_by_id(cls, id):
        ng = NotificationGroup.objects.filter(id=id)[:1]
        if ng:
            return ng[0]
        return None

    @classmethod
    @cachetools.cachedmethod(operator.attrgetter("_name_cache"), lock=lambda _: id_lock)
    def get_by_name(cls, name):
        ng = NotificationGroup.objects.filter(name=name)[:1]
        if ng:
            return ng[0]
        return None

    @property
    def members(self):
        """
        List of (time pattern, method, params, language)
        """
        default_language = LANGUAGE_CODE
        m = []
        # Collect user notifications
        for ngu in self.notificationgroupuser_set.filter(user__is_active=True):
            lang = ngu.user.preferred_language or default_language
            user_contacts = ngu.user.contacts
            if user_contacts:
                for tp, method, params in user_contacts:
                    m += [(TimePatternList([ngu.time_pattern, tp]), method, params, lang)]
            else:
                m += [(TimePatternList([]), "mail", ngu.user.email, lang)]
        # Collect other notifications
        for ngo in self.notificationgroupother_set.all():
            if ngo.notification_method == "mail" and "," in ngo.params:
                for y in ngo.params.split(","):
                    m += [(ngo.time_pattern, ngo.notification_method, y.strip(), default_language)]
            else:
                m += [(ngo.time_pattern, ngo.notification_method, ngo.params, default_language)]
        return m

    @property
    def active_members(self):
        """
        List of currently active members: (method, param, language)
        """
        now = datetime.datetime.now()
        return set(
            (method, param, lang) for tp, method, param, lang in self.members if tp.match(now)
        )

    @property
    def languages(self):
        """
        List of preferred languages for users
        """
        return set(x[3] for x in self.members)

    @classmethod
    def get_effective_message(cls, messages, lang):
        for cl in (lang, LANGUAGE_CODE, "en"):
            if cl in messages:
                return messages[cl]
        return "Cannot translate message"

    @classmethod
    def send_notification(cls, method, address, subject, body, attachments=None):
        topic = NOTIFICATION_TOPICS.get(method)
        if not topic:
            logging.error("Unknown notification method: %s", method)
            return
        logging.debug("Sending notification to %s via %s", address, method)
        pub(
            topic,
            {
                "address": address,
                "subject": subject,
                "body": body,
                "attachments": attachments or [],
            },
        )

    def notify(self, subject, body, link=None, attachments=None):
        """
        Send message to active members
        :param subject: Message subject
        :param body: Message body
        :param link: Optional link
        :param attachments: List of attachments. Each one is a dict
            with keys *filename* and *data*. *data* is the raw data
        """
        logger.debug("Notify group %s: %s", self.name, subject)
        if not isinstance(subject, dict):
            subject = {LANGUAGE_CODE: subject}
        if not isinstance(body, dict):
            body = {LANGUAGE_CODE: body}
        for method, params, lang in self.active_members:
            self.send_notification(
                method,
                params,
                self.get_effective_message(subject, lang),
                self.get_effective_message(body, lang),
                attachments,
            )

    @classmethod
    def group_notify(cls, groups, subject, body, link=None, delay=None, tag=None):
        """
        Send notification to a list of groups
        Prevent duplicated messages
        """
        if not subject and not body:
            return
        if subject is None:
            subject = ""
        if body is None:
            body = ""
        if not isinstance(subject, dict):
            subject = {LANGUAGE_CODE: subject}
        if not isinstance(body, dict):
            body = {LANGUAGE_CODE: body}
        ngs = set()
        lang = {}  # (method, params) -> lang
        for g in groups:
            for method, params, l in g.active_members:
                ngs.add((method, params))
                lang[(method, params)] = l
        for method, params in ngs:
            cls.send_notification(
                method,
                params,
                cls.get_effective_message(subject, lang[(method, params)]),
                cls.get_effective_message(body, lang[(method, params)]),
            )


class NotificationGroupUser(NOCModel):
    class Meta(object):
        verbose_name = "Notification Group User"
        verbose_name_plural = "Notification Group Users"
        app_label = "main"
        db_table = "main_notificationgroupuser"
        unique_together = [("notification_group", "time_pattern", "user")]

    notification_group = models.ForeignKey(
        NotificationGroup, verbose_name="Notification Group", on_delete=models.CASCADE
    )
    time_pattern = models.ForeignKey(
        TimePattern, verbose_name="Time Pattern", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE)

    def __str__(self):
        return "%s: %s: %s" % (
            self.notification_group.name,
            self.time_pattern.name,
            self.user.username,
        )


class NotificationGroupOther(NOCModel):
    class Meta(object):
        verbose_name = "Notification Group Other"
        verbose_name_plural = "Notification Group Others"
        app_label = "main"
        db_table = "main_notificationgroupother"
        unique_together = [("notification_group", "time_pattern", "notification_method", "params")]

    notification_group = models.ForeignKey(
        NotificationGroup, verbose_name="Notification Group", on_delete=models.CASCADE
    )
    time_pattern = models.ForeignKey(
        TimePattern, verbose_name="Time Pattern", on_delete=models.CASCADE
    )
    notification_method = models.CharField(
        "Method", max_length=16, choices=NOTIFICATION_METHOD_CHOICES
    )
    params = models.CharField("Params", max_length=256)

    def __str__(self):
        return "%s: %s: %s: %s" % (
            self.notification_group.name,
            self.time_pattern.name,
            self.notification_method,
            self.params,
        )

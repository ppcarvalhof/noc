# ---------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------
# Copyright (C) 2007-2022, The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import logging

# NOC modules
from noc.maintenance.models.maintenance import Maintenance
from noc.sa.models.managedobject import ManagedObject
from noc.fm.models.ttsystem import TTSystem
from noc.core.perf import metrics

logger = logging.getLogger(__name__)


def start_maintenance(maintenance_id):
    logger.info("[%s] Start maintenance", maintenance_id)
    m = Maintenance.get_by_id(maintenance_id)
    if not m:
        logger.info("[%s] Not found, skipping")
        return
    if not m.escalate_managed_object:
        logger.info("[%s] No managed object to escalate", maintenance_id)
        return
    if m.escalation_tt:
        logger.info("[%s] Already escalated as TT %s", maintenance_id, m.escalation_tt)
        return
    # Get external TT system
    tts_id = m.escalate_managed_object.tt_system_id
    if not tts_id:
        logger.info(
            "[%s] No TT mapping for object %s(%s)",
            maintenance_id,
            m.escalate_managed_object.name,
            m.escalate_managed_object.address,
        )
        return
    tt_system = m.escalate_managed_object.tt_system

    if not tt_system:
        logger.info("[%s] Cannot find TT system '%s'", maintenance_id, m.escalate_managed_object)
        return
    tts = tt_system.get_system()
    try:
        logger.info("[%s] Creating TT", maintenance_id)
        tt_id = tts.create_tt(
            queue=m.escalate_managed_object.tt_queue if m.escalate_managed_object.tt_queue else 1,
            obj=tts_id,
            reason="0",
            subject=m.subject,
            body=m.description or m.subject,
            login="correlator",
            timestamp=m.start,
        )
        logger.info("[%s] TT %s created", maintenance_id, tt_id)
        if tts.promote_group_tt:
            gtt = tts.create_group_tt(tt_id, m.start)
            SQL = """SELECT id, name, tt_system_id
                FROM sa_managedobject
                WHERE is_managed = 'true' AND affected_maintenances @> '{"%s": {}}';""" % str(
                maintenance_id
            )
            for mo in ManagedObject.objects.raw(SQL):
                logger.info("[%s] Appending object %s to group TT %s", maintenance_id, mo, gtt)
                tts.add_to_group_tt(gtt, mo.tt_system_id)
        if tt_id and not m.escalation_tt:
            m.escalation_tt = "%s:%s" % (m.escalate_managed_object.tt_system.name, tt_id)
            m.save()
        metrics["maintenance_tt_create"] += 1
    except tts.TTError as e:
        logger.error("[%s] Failed to escalate: %s", maintenance_id, e)
        metrics["maintenance_tt_fail"] += 1


def close_maintenance(maintenance_id):
    logger.info("[%s] Close maintenance", maintenance_id)
    m = Maintenance.get_by_id(maintenance_id)
    if not m:
        logger.info("[%s] Not found, skipping", maintenance_id)
        return
    if not m.escalation_tt:
        logger.info("[%s] Not escalated, skipping", maintenance_id)
        return
    tts_name, tt_id = m.escalation_tt.split(":", 1)
    tts = TTSystem.get_by_name(tts_name).get_system()
    if not tts:
        logger.error("[%s] TT system '%s' is not found", maintenance_id, tts_name)
        return
    try:
        logger.info("[%s] Closing TT %s", maintenance_id, tt_id)
        tts.close_tt(tt_id, subject="Closed", body="Closed", login="correlator")
        metrics["maintenance_tt_close"] += 1
    except tts.TTError as e:
        logger.error("[%s] Failed to close TT %s: %s", maintenance_id, tt_id, e)
        metrics["maintenance_tt_close_fail"] += 1

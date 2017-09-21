# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Strizh Hatch protocol collector
# ---------------------------------------------------------------------
# Copyright (C) 2007-2017 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import time
# Third-party modules
from tornado.web import RequestHandler, HTTPError
# NOC modules
from noc.core.perf import metrics
from noc.config import config
from noc.sa.models.managedobject import ManagedObject

Q_CPE_ID = "modem_id"
Q_DATA = "data"
Q_CPE_PROFILE = "Strizh.Hatch"

DOOR_CLS = {
    False: "Security | Door | Open",
    True: "Security | Door | Closed"
}

DOOR_STATUS = {
    True: "open",
    False: "closed"
}


class StrizhRequestHandler(RequestHandler):
    def initialize(self, service):
        self.service = service
        self.logger = service.logger

    def get(self, *args, **kwargs):
        metrics["webcollector_strizh_requests"] += 1
        # Check remote_address
        x_real_ip = self.request.headers.get("X-Real-IP")
        remote_ip = x_real_ip or self.request.remote_ip
        if remote_ip != config.webcollector.strizh_address:
            metrics["webcollector_strizh_invalid_source"] += 1
            self.logger.info("Invalid request source: %s", remote_ip)
            raise HTTPError(401, "Invalid address")
        # Get data
        data = self.get_arguments(Q_DATA)
        if not data or len(data[0]) < 2:
            self.logger.info("No data")
            metrics["webcollector_strizh_no_data"] += 1
            raise HTTPError(400, "No data")
        # Decode data to binary form
        data = [ord(c) for c in data[0].decode("hex")]
        # Get modem id
        modem_ids = self.get_arguments(Q_CPE_ID)
        if not modem_ids or not modem_ids[0]:
            metrics["webcollector_strizh_no_modem_id"] += 1
            self.logger.info("No modem_id")
            raise HTTPError(400, "Invalid modem id")
        cpe_id = modem_ids[0]
        # Get managed object by CPE ID
        mo = ManagedObject.get_by_global_cpe_id(cpe_id)
        if not mo:
            self.logger.info("Invalid CPE: %s", cpe_id)
            metrics["webcollector_strizh_invalid_cpe"] += 1
            raise HTTPError(404, "Invalid CPE")
        # @todo: Check profile
        if mo.profile.name != Q_CPE_PROFILE:
            self.logger.info("Invalid Profile: %s", mo.profile.name)
            metrics["webcollector_strizh_invalid_profile"] += 1
            raise HTTPError(404, "Invalid Profile")
        # Process data
        handler = getattr(self, "handle_0x%x" % data[0], None)
        if not handler:
            self.logger.info("Unklnown message type %x", data[0])
            metrics["webcollector_strizh_unknown_type"] += 1
            raise HTTPError(400, "Unknown message type")
        handler(mo, data)
        self.write("OK")

    @staticmethod
    def decode_voltage(v):
        """
        Voltage decoding formula
        U = 2 + (D>>7)+(D&0x7F)/100
        """
        return 2.0 + float(v >> 7) + float(v & 0x7f) / 100.0

    def handle_0x29(self, mo, data):
        """
        Self-diagnostics
        :param data:
        :return:
        """
        try:
            code, hw_ver, sw_ver, build, temp, voltage, flag, angle = data
        except ValueError:
            self.logger.info("Invalid message: %s", data)
            metrics["webcollector_strizh_invalid_format"] += 1
            raise HTTPError(400, "Invalid message format")
        voltage = self.decode_voltage(voltage)
        self.logger.info(
            "[%s|%s] Self-diagnostics: hw_ver=0x%x, sw_ver=0x%x, "
            "build=0x%x, temp=%dC, voltage=%fV, flags=%x, angle=%d",
            mo.name, mo.global_cpe_id,
            hw_ver, sw_ver, build, temp, voltage, flag, angle
        )

    def handle_0x80(self, mo, data):
        """
        Door open
        :param data:
        :return:
        """
        try:
            code, msg_id, angle, flag, temp, voltage, tx_power, zero = data
        except ValueError:
            self.logger.info("Invalid message: %s", data)
            metrics["webcollector_strizh_invalid_format"] += 1
            raise HTTPError(400, "Invalid message format")
        voltage = self.decode_voltage(voltage)
        is_open = angle >= config.webcollector.strizh_open_angle
        self.logger.info(
            "[%s|%s] Movement event: msg_id=%s, angle=%s (%s), flag=0x%x, temp=%s, "
            "voltage=%fV, tx_power=%ddBm",
            mo.name, mo.global_cpe_id,
            msg_id, angle,
            DOOR_STATUS[is_open],
            flag, temp, voltage, tx_power
        )
        self.service.register_message(
            mo.id,
            int(time.time()),
            {
                "source": "system",
                "$event": {
                    "class": DOOR_CLS[is_open],
                    "vars": {
                        "name": "manhole",
                        "angle": int(angle)
                    }
                }
            }
        )

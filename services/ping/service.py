#!./bin/python
# ---------------------------------------------------------------------
# Ping service
# ---------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import functools
import time
import datetime
import os
import asyncio
from typing import Dict, Any, Tuple, Optional, List

# Third-party modules
import orjson
from gufo.ping import Ping

# NOC modules
from noc.core.service.fastapi import FastAPIService
from noc.config import config
from noc.core.error import NOCError
from noc.core.ioloop.timers import PeriodicOffsetCallback
from noc.core.perf import metrics
from noc.services.ping.probesetting import ProbeSetting, Policy
from noc.services.ping.datastream import PingDataStreamClient


class PingService(FastAPIService):
    name = "ping"
    pooled = True
    process_name = "noc-%(name).10s-%(pool).5s"

    PING_CLS = {True: "NOC | Managed Object | Ping OK", False: "NOC | Managed Object | Ping Failed"}

    def __init__(self):
        super().__init__()
        self.mappings_callback = None
        self.probes = {}  # mo id -> ProbeSetting
        self.ping = None
        self.is_throttled = False
        self.slot_number = 0
        self.total_slots = 0
        self.ok_event = self.get_status_message(True)
        self.failed_event = self.get_status_message(False)
        self.pool_partitions: Dict[str, int] = {}

    async def on_activate(self):
        # Acquire slot
        self.slot_number, self.total_slots = await self.acquire_slot()
        if self.total_slots > 1:
            self.logger.info(
                "Enabling distributed mode: Slot %d/%d", self.slot_number, self.total_slots
            )
        else:
            self.logger.info("Enabling standalone mode")

        self.logger.info("Setting nice level to -20")
        try:
            os.nice(-20)
        except OSError as e:
            self.logger.info("Cannot set nice level to -20: %s", e)
        #
        metrics["down_objects"] = 0
        # Open ping sockets
        self.ping = Ping(tos=config.ping.tos)
        # Start tracking changes
        asyncio.get_running_loop().create_task(self.get_object_mappings())

    def get_mon_data(self):
        r = super().get_mon_data()
        r["throttled"] = self.is_throttled
        return r

    async def get_pool_partitions(self, pool: str) -> int:
        parts = self.pool_partitions.get(pool)
        if not parts:
            parts = await self.get_stream_partitions(ProbeSetting.get_pool_stream(pool))
            self.pool_partitions[pool] = parts
        return parts

    async def get_object_mappings(self):
        """
        Subscribe and track datastream changes
        """
        # Register RPC aliases
        client = PingDataStreamClient("cfgping", service=self)
        # Track stream changes
        while True:
            self.logger.info("Starting to track object mappings")
            try:
                await client.query(
                    limit=config.ping.ds_limit,
                    filters=[
                        "pool(%s)" % config.pool,
                        "shard(%d,%d)" % (self.slot_number, self.total_slots),
                    ],
                    block=True,
                    filter_policy="delete",
                )
            except NOCError as e:
                self.logger.info("Failed to get object mappings: %s", e)
                await asyncio.sleep(1)

    async def update_probe(self, data):
        if data["id"] in self.probes:
            await self._change_probe(data)
        else:
            await self._create_probe(data)

    async def delete_probe(self, id):
        if id not in self.probes:
            return
        ps = self.probes[id]
        ip = self.probes[id].address
        self.logger.info("Delete probe: %s", ip)
        ps.task.stop()
        ps.task = None
        del self.probes[id]
        metrics["ping_probe_delete"] += 1
        if ps.status is not None and not ps.status:
            metrics["down_objects"] -= 1
        metrics["ping_objects"] = len(self.probes)

    async def _create_probe(self, data):
        """
        Create new ping probe
        """
        self.logger.info("Create probe: %s (%ds)", data["address"], data["interval"])
        ps = ProbeSetting(**data)
        ps.set_partition(await self.get_pool_partitions(ps.fm_pool))
        self.probes[data["id"]] = ps
        pt = PeriodicOffsetCallback(functools.partial(self.ping_check, ps), ps.interval * 1000)
        ps.task = pt
        pt.start()
        metrics["ping_probe_create"] += 1
        metrics["ping_objects"] = len(self.probes)

    async def _change_probe(self, data):
        self.logger.info("Update probe: %s (%ds)", data["address"], data["interval"])
        ps = self.probes[data["id"]]
        if ps.interval != data["interval"]:
            ps.task.set_interval(data["interval"] * 1000)
        if ps.address != data["address"]:
            self.logger.info("Changing address: %s -> %s", ps.address, data["address"])
            ps.address = data["address"]
        if ps.fm_pool != data["fm_pool"]:
            ps.fm_pool = data["fm_pool"]
            ps.set_stream()
            ps.set_partition(await self.get_pool_partitions(ps.fm_pool))
        ps.update(**data)
        metrics["ping_probe_update"] += 1
        metrics["ping_objects"] = len(self.probes)

    @classmethod
    def get_status_message(cls, status: bool) -> Dict[str, Any]:
        """
        Construct status message event
        :param status:
        :return:
        """
        return {"source": "system", "$event": {"class": cls.PING_CLS[status], "vars": {}}}

    async def _probe(self, ps: ProbeSetting) -> Tuple[Optional[float], int]:
        """
        Perform ping probe.

        Args:
            ps: ProbeSettings instance.

        Returns:
            Tuple of (Average RTT or None, Attempts)
        """
        attempts = 0
        timings: List[float] = []
        async for rtt in self.ping.iter_rtt(
            ps.address, size=ps.size, count=ps.count, interval=ps.timeout
        ):
            if rtt is not None and ps.policy == Policy.CHECK_FIRST:
                if attempts > 0:
                    metrics["ping_check_recover"] += 1
                return rtt, attempts  # Quit of first success
            elif rtt is None and ps.policy == Policy.CHECK_ALL:
                return None, 0  # Quit on first failure
            elif rtt is not None:
                timings.append(rtt)
            attempts += 1
        if not timings:
            return None, 0  # No success
        # CHECK_ALL policy
        return sum(timings) / len(timings), 0

    async def ping_check(self, ps: ProbeSetting) -> None:
        """
        Perform ping check and set result.

        Args:
            ps: ProbeSettings instance.
        """
        if ps.id not in self.probes:
            return
        address = ps.address
        t0 = time.time()
        metrics["ping_check_total"] += 1
        disable_message = False  # Disabe sent Event message
        if ps.time_cond:
            dt = datetime.datetime.fromtimestamp(t0)
            if not eval(ps.time_cond, {"T": dt}):
                if ps.expr_policy == "D":
                    metrics["ping_check_skips"] += 1
                    return
                if ps.expr_policy == "E":
                    self.logger.info("[%s] Disabled message", address)
                    disable_message = True
        # Check
        rtt, attempts = await self._probe(ps)
        s = rtt is not None
        if s:
            metrics["ping_check_success"] += 1
            self.logger.debug("[%s] Result: success, rtt=%s, attempt=%d", address, rtt, attempts)
        else:
            metrics["ping_check_fail"] += 1
            self.logger.debug("[%s] Result: failed", address)
        if s and not rtt:
            metrics["ping_time_stepbacks"] += 1
        if ps and s != ps.status:
            if s:
                metrics["down_objects"] -= 1
            else:
                metrics["down_objects"] += 1
            if config.ping.throttle_threshold:
                # Process throttling
                down_ratio = float(metrics["down_objects"]) * 100.0 / float(metrics["ping_objects"])
                if self.is_throttled:
                    restore_ratio = config.ping.restore_threshold or config.ping.throttle_threshold
                    if down_ratio <= restore_ratio:
                        self.logger.info(
                            "Leaving throttling mode (%s%% <= %s%%)", down_ratio, restore_ratio
                        )
                        self.is_throttled = False
                        # @todo: Send unthrottling message
                elif down_ratio > config.ping.throttle_threshold:
                    self.logger.info(
                        "Entering throttling mode (%s%% > %s%%)",
                        down_ratio,
                        config.ping.throttle_threshold,
                    )
                    self.is_throttled = True
                    # @todo: Send throttling message
            ts = " (Throttled)" if self.is_throttled else ""
            self.logger.info("[%s] Changing status to %s%s", address, s, ts)
            ps.status = s
        if ps and not self.is_throttled and not disable_message and s != ps.sent_status:
            self.publish(
                orjson.dumps(
                    {"ts": t0, "object": ps.id, "data": self.ok_event if s else self.failed_event}
                ),
                stream=ps.stream,
                partition=ps.partition,
            )
            ps.sent_status = s
        self.logger.debug("[%s] status=%s rtt=%s", address, s, rtt)
        # Send RTT and attempts metrics
        to_report_rtt = rtt is not None and ps.report_rtt
        if (to_report_rtt or ps.report_attempts) and ps.bi_id:
            lt = time.localtime(t0)
            ts = time.strftime("%Y-%m-%d %H:%M:%S", lt)
            date = ts.split(" ")[0]
            data = {"date": date, "ts": ts, "managed_object": ps.bi_id}
            if to_report_rtt:
                data["rtt"] = int(rtt * 1000000)
            if ps.report_attempts:
                data["attempts"] = attempts
            self.register_metrics("ping", [data], key=ps.bi_id)


if __name__ == "__main__":
    PingService().start()

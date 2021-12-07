#!./bin/python
# ---------------------------------------------------------------------
# mrt service
# ---------------------------------------------------------------------
# Copyright (C) 2007-2016 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.service.fastapi import FastAPIService
from noc.config import config


class MRTService(FastAPIService):
    name = "mrt"
    use_telemetry = config.mrt.enable_command_logging
    use_mongo = True

    if config.features.traefik:
        traefik_backend = "mrt"
        traefik_frontend_rule = "PathPrefix:/api/mrt"

    async def on_activate(self):
        self.sae = self.open_rpc("sae")


if __name__ == "__main__":
    MRTService().start()

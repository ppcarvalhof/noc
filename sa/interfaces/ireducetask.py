# ---------------------------------------------------------------------
# IReduceTask interface
# ---------------------------------------------------------------------
# Copyright (C) 2007-2010 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC Modules
from noc.core.interface.base import BaseInterface
from .base import InstanceOfParameter


class IReduceTask(BaseInterface):
    task = InstanceOfParameter("ReduceTask")

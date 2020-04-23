# ---------------------------------------------------------------------
# IGetIfIndex - Get ifIndex by interface name
# ---------------------------------------------------------------------
# Copyright (C) 2007-2009 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.core.interface.base import BaseInterface
from .base import InterfaceNameParameter, IntParameter, NoneParameter


class IGetIfIndex(BaseInterface):
    interface = InterfaceNameParameter()
    returns = IntParameter() | NoneParameter()

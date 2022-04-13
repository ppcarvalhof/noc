# ----------------------------------------------------------------------
# DataSource Base
# ----------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from dataclasses import dataclass
from functools import partial

# Third-party modules
import pandas as pd

# NOC modules
from typing import Optional, Dict, Any, Iterable, List


@dataclass
class FieldInfo(object):
    name: str
    description: Optional[str] = None
    internal_name: Optional[str] = None
    type: str = "string"


class BaseDataSource(object):
    """DataSource and fields description"""

    name: str
    fields: List[FieldInfo]

    @classmethod
    def query_sync(cls, fields: Optional[Iterable[str]] = None, *args, **kwargs) -> pd.DataFrame:
        from noc.core.ioloop.util import run_sync

        return run_sync(partial(cls.query, fields, *args, **kwargs))

    @classmethod
    async def query(cls, fields: Optional[Iterable[str]] = None, *args, **kwargs) -> pd.DataFrame:
        ...

    @classmethod
    async def iter_query(
        cls, fields: Optional[Iterable[str]] = None, *args, **kwargs
    ) -> Iterable[Dict[str, Any]]:
        ...

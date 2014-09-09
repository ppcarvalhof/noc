## -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## Probe base class
##----------------------------------------------------------------------
## Copyright (C) 2007-2014 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------

## Python modules
import os
import inspect
import time
from collections import defaultdict
from collections import namedtuple
import logging
## NOC modules
from noc.lib.solutions import solutions_roots
from match import MatchExpr, MatchTrue
import noc.lib.snmp.version
from noc.lib.snmp.error import SNMPError, NO_SUCH_NAME


HandlerItem = namedtuple("HandlerItem", [
    "handler", "handler_name", "match", "req", "opt", "preference",
    "convert", "scale"
])

logger = logging.getLogger(__name__)


class ProbeRegistry(object):
    def __init__(self):
        self.loaded = False
        self.probes = defaultdict(list)  #  metric type -> [HandlerItem]
        self.handlers = {}  # name -> callable

    def load_all(self):
        if self.loaded:
            return
        # Get all probes locations
        dirs = ["pm/probes"]
        for r in solutions_roots():
            d = os.path.join(r, "pm", "probes")
            if os.path.isdir(d):
                dirs += [d]
        # Load all probes
        for root in dirs:
            for path, dirnames, filenames in os.walk(root):
                for f in filenames:
                    if not f.endswith(".py") or f == "__init__.py":
                        continue
                    fp = os.path.join(path, f)
                    mn = "noc.%s" % fp[:-3].replace(os.path.sep, ".")
                    __import__(mn, {}, {}, "*")
        # Order probes by preference
        for mt in self.probes:
            self.probes[mt] = sorted(self.probes[mt],
                                     key=lambda x: x.preference)
        # Prevent further loading
        self.loaded = True

    def register(self, handler, match, req, opt, preference, convert,
                 scale):
        for mt in handler._metrics:
            hname = self.get_handler_name(handler)
            self.probes[mt] += [
                HandlerItem(
                    handler=handler,
                    handler_name=hname, match=match,
                    req=req, opt=opt, preference=preference,
                    convert=convert, scale=scale
                )
            ]
            self.handlers[hname] = handler

    def iter_handlers(self, metric_type):
        for h in self.probes[metric_type]:
            yield h

    @classmethod
    def get_handler_name(cls, v):
        return "%s.%s.%s" % (
            v.im_class.__module__,
            v.im_class.__name__,
            v.__name__)

    def get_handler(self, name):
        return self.handlers[name]


probe_registry = ProbeRegistry()


class ProbeBase(type):
    def __new__(cls, name, bases, attrs):
        m = type.__new__(cls, name, bases, attrs)
        # Get all decorated members
        for name, value in inspect.getmembers(m):
            # @todo: better checks for unbound methods
            if hasattr(value, "_metrics"):
                mx = value._match_expr
                if not mx:
                    mx = MatchTrue()
                elif len(mx) == 1:
                    mx = mx[0]
                else:
                    mx = reduce(lambda x, y: x | y, mx)
                r, o = mx.get_vars()
                r |= set(value._required_config)
                o |= set(value._opt_config)
                o -= r
                probe_registry.register(
                    value, mx.compile(), r, o,
                    value._preference, value._convert, value._scale
                )
        return m


class Probe(object):
    __metaclass__ = ProbeBase

    SNMP_v2c = noc.lib.snmp.version.SNMP_v2c

    INVALID_OID_TTL = 3600

    def __init__(self, daemon):
        self.daemon = daemon
        self.missed_oids = {}  # oid -> expire time

    def disable(self):
        raise NotImplementedError()

    def is_missed_oid(self, oid):
        t = self.missed_oids.get(oid)
        if t:
            if t > time.time():
                return True
            else:
                del self.missed_oids[oid]
        return False

    def set_missed_oid(self, oid):
        logger.info("Disabling missed oid %s", oid)
        self.missed_oids[oid] = time.time() + self.INVALID_OID_TTL

    def snmp_get(self, oids, address, port=161,
                 community="public", version=SNMP_v2c):
        """
        Perform SNMP request to one or more OIDs.
        oids can be string or dict.
        When oid is string returns value
        When oid is dict of <metric type> : oid, returns
        dict of <metric type>: value
        """
        def first_valid(oids):
            if isinstance(oids, basestring):
                if not self.is_missed_oid(oids):
                    return oids
            else:
                for oid in oids:
                    if not self.is_missed_oid(oid):
                        return oid
            return None

        def iter_oids(oids):
            if isinstance(oids, basestring):
                # OID is string
                if not self.is_missed_oid(oids):
                    yield oids
            elif isinstance(oids, dict) and oids:
                r = {}
                for k, v in oids.iteritems():
                    v = first_valid(v)
                    if v is None:
                        raise StopIteration()
                    r[k] = v
                yield r

        while True:
            to_continue = False
            for o in iter_oids(oids):
                try:
                    return self.daemon.io.snmp_get(
                        o, address, port,
                        community=community,
                        version=version)
                except SNMPError, why:
                    if why.code == NO_SUCH_NAME:
                        # Disable invalid oid
                        self.set_missed_oid(why.oid)
                        to_continue = True
                        break  # Restart
                    else:
                        return None
            if not to_continue:
                logger.info("No valid OIDs to poll")
                break


class metric(object):
    # Standard preferences
    PREF_VERSION = 100  # Version-depended implementations
    PREF_MODEL = 200  # Model-depended implementations
    PREF_PLATFORM = 300  # Platform-depended implementations
    PREF_VENDOR = 400  # Vendor-depended implementations
    PREF_COMMON = 500  # Common fallback implementations
    # Preferences adjustments
    PREF_BETTER = -10
    PREF_WORSE = 10

    # Conversion methods
    NONE = "none"
    COUNTER = "counter"

    MATCH_OPS = ["eq", "in"]

    def __init__(self, metrics, preference=PREF_COMMON, convert=NONE,
                 scale=1.0, **kwargs):
        if isinstance(metrics, basestring):
            metrics = [metrics]
        self.metrics = metrics
        self.preference = preference
        self.convert = convert
        self.scale = scale
        self.selector = kwargs

    def __call__(self, f):
        f._metrics = self.metrics
        f._preference = self.preference
        # Get config options
        spec = inspect.getargspec(f)
        rv, ov = spec.args[1:], []
        if spec.defaults is not None:
            dl = len(spec.defaults)
            ov, rv = rv[-dl:], rv[:-dl]
        # Get match variables
        xrv = getattr(f, "_required_config", [])
        xov = getattr(f, "_opt_config", [])
        mx = getattr(f, "_match_expr", [])
        f._match_expr = mx + self.parse_match(self.selector)
        rv = list(set(xrv + rv))
        ov = list(set(xov + ov) - set(rv))
        #
        f._required_config = rv
        f._opt_config = ov
        f._preference = self.preference
        f._convert = self.convert
        f._scale = self.scale
        return f

    def parse_match(self, match):
        """
        Returns a tuple of parsed match expressions
        """
        mx = []
        for var in match:
            mv, op = var.rsplit("__", 1)
            if op not in self.MATCH_OPS:
                mv, op = var, "eq"
            mx += [MatchExpr.create(mv, op, match[var])]
        if not len(mx):
            return []
        elif len(mx) == 1:
            return mx
        else:
            return [reduce(lambda x, y: x & y, mx)]


probe_registry.load_all()

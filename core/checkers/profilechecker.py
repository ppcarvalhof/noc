# ----------------------------------------------------------------------
# Profile checker
# ----------------------------------------------------------------------
# Copyright (C) 2007-2022 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Python modules
from typing import List, Iterable

# NOC modules
from noc.core.text import filter_non_printable
from .base import ObjectChecker, CheckResult, ProfileSet
from ..profile.checker import ProfileChecker as ProfileCheckerProfile
from ..script.credentialchecker import Protocol
from ..wf.diagnostic import DiagnosticState, SNMP_DIAG


class ProfileChecker(ObjectChecker):
    """
    Check ManagedObject profile by rules
    """

    name = "profilechecker"
    CHECKS: List[str] = ["PROFILE"]
    USER_DISCOVERY_USE = False
    CHECK_SNMP_VERSION_MAP = {
        p.config.check: p.config.snmp_version
        for p in Protocol
        if p.config.snmp_version is not None and p.config.check
    }

    def iter_result(self, checks=None) -> Iterable[CheckResult]:
        if (
            SNMP_DIAG in self.object.diagnostics
            and self.object.get_diagnostic(SNMP_DIAG).state == DiagnosticState.enabled
        ):
            snmp_community = self.object.credentials.snmp_ro
            snmp_version = [
                self.CHECK_SNMP_VERSION_MAP[check.name]
                for check in self.object.get_diagnostic(SNMP_DIAG).checks or []
                if check.status
            ]
        else:
            snmp_community, snmp_version = None, []
        checker = ProfileCheckerProfile(
            self.object.address,
            self.object.pool.name,
            logger=self.logger,
            calling_service=self.calling_service,
            snmp_community=snmp_community,
            snmp_version=snmp_version,
        )
        profile = checker.get_profile()
        if not profile:
            yield CheckResult(
                check="PROFILE",
                status=bool(profile),
                error=filter_non_printable(checker.get_error())[:200],
            )
            return
        # Skipped
        yield CheckResult(
            check="PROFILE",
            status=bool(profile),
            data={"profile": profile.name},
            action=ProfileSet(profile=profile.name),
        )

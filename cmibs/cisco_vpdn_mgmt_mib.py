# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# CISCO-VPDN-MGMT-MIB
# Compiled MIB
# Do not modify this file directly
# Run ./noc mib make-cmib instead
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# MIB Name
NAME = "CISCO-VPDN-MGMT-MIB"

# Metadata
LAST_UPDATED = "2009-06-16"
COMPILED = "2020-01-19"

# MIB Data: name -> oid
MIB = {
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIB": "1.3.6.1.4.1.9.10.24",
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIBNotifs": "1.3.6.1.4.1.9.10.24.0",
    "CISCO-VPDN-MGMT-MIB::cvpdnNotifSessionID": "1.3.6.1.4.1.9.10.24.0.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnNotifSessionEvent": "1.3.6.1.4.1.9.10.24.0.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnNotifSession": "1.3.6.1.4.1.9.10.24.0.3",
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIBObjects": "1.3.6.1.4.1.9.10.24.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemInfo": "1.3.6.1.4.1.9.10.24.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelTotal": "1.3.6.1.4.1.9.10.24.1.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionTotal": "1.3.6.1.4.1.9.10.24.1.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnDeniedUsersTotal": "1.3.6.1.4.1.9.10.24.1.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemTable": "1.3.6.1.4.1.9.10.24.1.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemEntry": "1.3.6.1.4.1.9.10.24.1.1.4.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemTunnelType": "1.3.6.1.4.1.9.10.24.1.1.4.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemTunnelTotal": "1.3.6.1.4.1.9.10.24.1.1.4.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemSessionTotal": "1.3.6.1.4.1.9.10.24.1.1.4.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemDeniedUsersTotal": "1.3.6.1.4.1.9.10.24.1.1.4.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemInitialConnReq": "1.3.6.1.4.1.9.10.24.1.1.4.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemSuccessConnReq": "1.3.6.1.4.1.9.10.24.1.1.4.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemFailedConnReq": "1.3.6.1.4.1.9.10.24.1.1.4.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemNotifSessionEnabled": "1.3.6.1.4.1.9.10.24.1.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnSystemClearSessions": "1.3.6.1.4.1.9.10.24.1.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelInfo": "1.3.6.1.4.1.9.10.24.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelTable": "1.3.6.1.4.1.9.10.24.1.2.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelEntry": "1.3.6.1.4.1.9.10.24.1.2.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelTunnelId": "1.3.6.1.4.1.9.10.24.1.2.1.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelRemoteTunnelId": "1.3.6.1.4.1.9.10.24.1.2.1.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelLocalName": "1.3.6.1.4.1.9.10.24.1.2.1.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelRemoteName": "1.3.6.1.4.1.9.10.24.1.2.1.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelRemoteEndpointName": "1.3.6.1.4.1.9.10.24.1.2.1.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelLocalInitConnection": "1.3.6.1.4.1.9.10.24.1.2.1.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelOrigCause": "1.3.6.1.4.1.9.10.24.1.2.1.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelState": "1.3.6.1.4.1.9.10.24.1.2.1.1.8",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelActiveSessions": "1.3.6.1.4.1.9.10.24.1.2.1.1.9",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelDeniedUsers": "1.3.6.1.4.1.9.10.24.1.2.1.1.10",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSoftshut": "1.3.6.1.4.1.9.10.24.1.2.1.1.12",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelNetworkServiceType": "1.3.6.1.4.1.9.10.24.1.2.1.1.13",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelLocalIpAddress": "1.3.6.1.4.1.9.10.24.1.2.1.1.14",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSourceIpAddress": "1.3.6.1.4.1.9.10.24.1.2.1.1.15",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelRemoteIpAddress": "1.3.6.1.4.1.9.10.24.1.2.1.1.16",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrTable": "1.3.6.1.4.1.9.10.24.1.2.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrEntry": "1.3.6.1.4.1.9.10.24.1.2.2.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrTunnelId": "1.3.6.1.4.1.9.10.24.1.2.2.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteTunnelId": "1.3.6.1.4.1.9.10.24.1.2.2.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrLocalName": "1.3.6.1.4.1.9.10.24.1.2.2.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteName": "1.3.6.1.4.1.9.10.24.1.2.2.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteEndpointName": "1.3.6.1.4.1.9.10.24.1.2.2.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrLocalInitConnection": "1.3.6.1.4.1.9.10.24.1.2.2.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrOrigCause": "1.3.6.1.4.1.9.10.24.1.2.2.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrState": "1.3.6.1.4.1.9.10.24.1.2.2.1.8",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrActiveSessions": "1.3.6.1.4.1.9.10.24.1.2.2.1.9",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrDeniedUsers": "1.3.6.1.4.1.9.10.24.1.2.2.1.10",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrSoftshut": "1.3.6.1.4.1.9.10.24.1.2.2.1.11",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrNetworkServiceType": "1.3.6.1.4.1.9.10.24.1.2.2.1.12",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrLocalIpAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.13",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrSourceIpAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.14",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteIpAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.15",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrLocalInetAddressType": "1.3.6.1.4.1.9.10.24.1.2.2.1.16",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrLocalInetAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.17",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrSourceInetAddressType": "1.3.6.1.4.1.9.10.24.1.2.2.1.18",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrSourceInetAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.19",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteInetAddressType": "1.3.6.1.4.1.9.10.24.1.2.2.1.20",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelAttrRemoteInetAddress": "1.3.6.1.4.1.9.10.24.1.2.2.1.21",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionInfo": "1.3.6.1.4.1.9.10.24.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionTable": "1.3.6.1.4.1.9.10.24.1.3.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionEntry": "1.3.6.1.4.1.9.10.24.1.3.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionId": "1.3.6.1.4.1.9.10.24.1.3.1.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionUserName": "1.3.6.1.4.1.9.10.24.1.3.1.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionState": "1.3.6.1.4.1.9.10.24.1.3.1.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionCallDuration": "1.3.6.1.4.1.9.10.24.1.3.1.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionPacketsOut": "1.3.6.1.4.1.9.10.24.1.3.1.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionBytesOut": "1.3.6.1.4.1.9.10.24.1.3.1.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionPacketsIn": "1.3.6.1.4.1.9.10.24.1.3.1.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionBytesIn": "1.3.6.1.4.1.9.10.24.1.3.1.1.8",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDeviceType": "1.3.6.1.4.1.9.10.24.1.3.1.1.9",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDeviceCallerId": "1.3.6.1.4.1.9.10.24.1.3.1.1.10",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDevicePhyId": "1.3.6.1.4.1.9.10.24.1.3.1.1.11",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionMultilink": "1.3.6.1.4.1.9.10.24.1.3.1.1.12",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionModemSlotIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.13",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionModemPortIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.14",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDS1SlotIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.15",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDS1PortIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.16",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionDS1ChannelIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.17",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionModemCallStartTime": "1.3.6.1.4.1.9.10.24.1.3.1.1.18",
    "CISCO-VPDN-MGMT-MIB::cvpdnTunnelSessionModemCallStartIndex": "1.3.6.1.4.1.9.10.24.1.3.1.1.19",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrTable": "1.3.6.1.4.1.9.10.24.1.3.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrEntry": "1.3.6.1.4.1.9.10.24.1.3.2.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrSessionId": "1.3.6.1.4.1.9.10.24.1.3.2.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrUserName": "1.3.6.1.4.1.9.10.24.1.3.2.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrState": "1.3.6.1.4.1.9.10.24.1.3.2.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrCallDuration": "1.3.6.1.4.1.9.10.24.1.3.2.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrPacketsOut": "1.3.6.1.4.1.9.10.24.1.3.2.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrBytesOut": "1.3.6.1.4.1.9.10.24.1.3.2.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrPacketsIn": "1.3.6.1.4.1.9.10.24.1.3.2.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrBytesIn": "1.3.6.1.4.1.9.10.24.1.3.2.1.8",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDeviceType": "1.3.6.1.4.1.9.10.24.1.3.2.1.9",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDeviceCallerId": "1.3.6.1.4.1.9.10.24.1.3.2.1.10",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDevicePhyId": "1.3.6.1.4.1.9.10.24.1.3.2.1.11",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrMultilink": "1.3.6.1.4.1.9.10.24.1.3.2.1.12",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrModemSlotIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.13",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrModemPortIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.14",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDS1SlotIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.15",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDS1PortIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.16",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrDS1ChannelIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.17",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrModemCallStartTime": "1.3.6.1.4.1.9.10.24.1.3.2.1.18",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrModemCallStartIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.19",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrVirtualCircuitID": "1.3.6.1.4.1.9.10.24.1.3.2.1.20",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrSentPktsDropped": "1.3.6.1.4.1.9.10.24.1.3.2.1.21",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrRecvPktsDropped": "1.3.6.1.4.1.9.10.24.1.3.2.1.22",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrMultilinkBundle": "1.3.6.1.4.1.9.10.24.1.3.2.1.23",
    "CISCO-VPDN-MGMT-MIB::cvpdnSessionAttrMultilinkIfIndex": "1.3.6.1.4.1.9.10.24.1.3.2.1.24",
    "CISCO-VPDN-MGMT-MIB::cvpdnUserToFailHistInfo": "1.3.6.1.4.1.9.10.24.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnUserToFailHistInfoTable": "1.3.6.1.4.1.9.10.24.1.4.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnUserToFailHistInfoEntry": "1.3.6.1.4.1.9.10.24.1.4.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistUname": "1.3.6.1.4.1.9.10.24.1.4.1.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistTunnelId": "1.3.6.1.4.1.9.10.24.1.4.1.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistUserId": "1.3.6.1.4.1.9.10.24.1.4.1.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistLocalInitConn": "1.3.6.1.4.1.9.10.24.1.4.1.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistLocalName": "1.3.6.1.4.1.9.10.24.1.4.1.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistRemoteName": "1.3.6.1.4.1.9.10.24.1.4.1.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistSourceIp": "1.3.6.1.4.1.9.10.24.1.4.1.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistDestIp": "1.3.6.1.4.1.9.10.24.1.4.1.1.8",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistCount": "1.3.6.1.4.1.9.10.24.1.4.1.1.9",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistFailTime": "1.3.6.1.4.1.9.10.24.1.4.1.1.10",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistFailType": "1.3.6.1.4.1.9.10.24.1.4.1.1.11",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistFailReason": "1.3.6.1.4.1.9.10.24.1.4.1.1.12",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistSourceInetType": "1.3.6.1.4.1.9.10.24.1.4.1.1.13",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistSourceInetAddr": "1.3.6.1.4.1.9.10.24.1.4.1.1.14",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistDestInetType": "1.3.6.1.4.1.9.10.24.1.4.1.1.15",
    "CISCO-VPDN-MGMT-MIB::cvpdnUnameToFailHistDestInetAddr": "1.3.6.1.4.1.9.10.24.1.4.1.1.16",
    "CISCO-VPDN-MGMT-MIB::cvpdnTemplateInfo": "1.3.6.1.4.1.9.10.24.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnTemplateTable": "1.3.6.1.4.1.9.10.24.1.5.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTemplateEntry": "1.3.6.1.4.1.9.10.24.1.5.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTemplateName": "1.3.6.1.4.1.9.10.24.1.5.1.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnTemplateActiveSessions": "1.3.6.1.4.1.9.10.24.1.5.1.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnMultilinkInfo": "1.3.6.1.4.1.9.10.24.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundlesWithOneLink": "1.3.6.1.4.1.9.10.24.1.6.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundlesWithTwoLinks": "1.3.6.1.4.1.9.10.24.1.6.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundlesWithMoreThanTwoLinks": "1.3.6.1.4.1.9.10.24.1.6.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleTable": "1.3.6.1.4.1.9.10.24.1.6.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleEntry": "1.3.6.1.4.1.9.10.24.1.6.4.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleName": "1.3.6.1.4.1.9.10.24.1.6.4.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleLinkCount": "1.3.6.1.4.1.9.10.24.1.6.4.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleEndpointType": "1.3.6.1.4.1.9.10.24.1.6.4.1.3",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleEndpoint": "1.3.6.1.4.1.9.10.24.1.6.4.1.4",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundlePeerIpAddrType": "1.3.6.1.4.1.9.10.24.1.6.4.1.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundlePeerIpAddr": "1.3.6.1.4.1.9.10.24.1.6.4.1.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleEndpointClass": "1.3.6.1.4.1.9.10.24.1.6.4.1.7",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleLastChanged": "1.3.6.1.4.1.9.10.24.1.6.5",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleChildTable": "1.3.6.1.4.1.9.10.24.1.6.6",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleChildEntry": "1.3.6.1.4.1.9.10.24.1.6.6.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleChildTunnelType": "1.3.6.1.4.1.9.10.24.1.6.6.1.1",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleChildTunnelId": "1.3.6.1.4.1.9.10.24.1.6.6.1.2",
    "CISCO-VPDN-MGMT-MIB::cvpdnBundleChildSessionId": "1.3.6.1.4.1.9.10.24.1.6.6.1.3",
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIBConformance": "1.3.6.1.4.1.9.10.24.3",
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIBCompliances": "1.3.6.1.4.1.9.10.24.3.1",
    "CISCO-VPDN-MGMT-MIB::ciscoVpdnMgmtMIBGroups": "1.3.6.1.4.1.9.10.24.3.2",
}

DISPLAY_HINTS = {}

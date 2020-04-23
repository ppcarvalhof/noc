# ----------------------------------------------------------------------
# HUAWEI-DEVICE-MIB
# Compiled MIB
# Do not modify this file directly
# Run ./noc mib make-cmib instead
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# MIB Name
NAME = "HUAWEI-DEVICE-MIB"

# Metadata
LAST_UPDATED = "2004-06-28"
COMPILED = "2020-01-19"

# MIB Data: name -> oid
MIB = {
    "HUAWEI-DEVICE-MIB::hwSystemPara": "1.3.6.1.4.1.2011.6.3.1",
    "HUAWEI-DEVICE-MIB::hwSysIpAddr": "1.3.6.1.4.1.2011.6.3.1.1",
    "HUAWEI-DEVICE-MIB::hwSysIpMask": "1.3.6.1.4.1.2011.6.3.1.2",
    "HUAWEI-DEVICE-MIB::hwSysVersion": "1.3.6.1.4.1.2011.6.3.1.3",
    "HUAWEI-DEVICE-MIB::hwSysTime": "1.3.6.1.4.1.2011.6.3.1.4",
    "HUAWEI-DEVICE-MIB::hwNmsParaTable": "1.3.6.1.4.1.2011.6.3.2",
    "HUAWEI-DEVICE-MIB::hwNmsParaEntry": "1.3.6.1.4.1.2011.6.3.2.1",
    "HUAWEI-DEVICE-MIB::hwNmsIndex": "1.3.6.1.4.1.2011.6.3.2.1.1",
    "HUAWEI-DEVICE-MIB::hwNmsName": "1.3.6.1.4.1.2011.6.3.2.1.2",
    "HUAWEI-DEVICE-MIB::hwNmsIp": "1.3.6.1.4.1.2011.6.3.2.1.3",
    "HUAWEI-DEVICE-MIB::hwNmsMask": "1.3.6.1.4.1.2011.6.3.2.1.4",
    "HUAWEI-DEVICE-MIB::hwNmsMaintainMode": "1.3.6.1.4.1.2011.6.3.2.1.5",
    "HUAWEI-DEVICE-MIB::hwNmsGetCommunity": "1.3.6.1.4.1.2011.6.3.2.1.6",
    "HUAWEI-DEVICE-MIB::hwNmsSetCommunity": "1.3.6.1.4.1.2011.6.3.2.1.7",
    "HUAWEI-DEVICE-MIB::hwNmsSnmpPort": "1.3.6.1.4.1.2011.6.3.2.1.8",
    "HUAWEI-DEVICE-MIB::hwNmsTrapPort": "1.3.6.1.4.1.2011.6.3.2.1.9",
    "HUAWEI-DEVICE-MIB::hwNmsClass": "1.3.6.1.4.1.2011.6.3.2.1.10",
    "HUAWEI-DEVICE-MIB::hwNmsStatus": "1.3.6.1.4.1.2011.6.3.2.1.11",
    "HUAWEI-DEVICE-MIB::hwSlotConf": "1.3.6.1.4.1.2011.6.3.3",
    "HUAWEI-DEVICE-MIB::hwFrameTable": "1.3.6.1.4.1.2011.6.3.3.1",
    "HUAWEI-DEVICE-MIB::hwFrameEntry": "1.3.6.1.4.1.2011.6.3.3.1.1",
    "HUAWEI-DEVICE-MIB::hwFrameIndex": "1.3.6.1.4.1.2011.6.3.3.1.1.1",
    "HUAWEI-DEVICE-MIB::hwFrameType": "1.3.6.1.4.1.2011.6.3.3.1.1.2",
    "HUAWEI-DEVICE-MIB::hwFrameDesc": "1.3.6.1.4.1.2011.6.3.3.1.1.3",
    "HUAWEI-DEVICE-MIB::hwSlots": "1.3.6.1.4.1.2011.6.3.3.1.1.4",
    "HUAWEI-DEVICE-MIB::hwFrameOperStatus": "1.3.6.1.4.1.2011.6.3.3.1.1.5",
    "HUAWEI-DEVICE-MIB::hwFrameAdminStatus": "1.3.6.1.4.1.2011.6.3.3.1.1.6",
    "HUAWEI-DEVICE-MIB::hwFrameRowStatus": "1.3.6.1.4.1.2011.6.3.3.1.1.7",
    "HUAWEI-DEVICE-MIB::hwSlotTable": "1.3.6.1.4.1.2011.6.3.3.2",
    "HUAWEI-DEVICE-MIB::hwSlotEntry": "1.3.6.1.4.1.2011.6.3.3.2.1",
    "HUAWEI-DEVICE-MIB::hwSlotIndex": "1.3.6.1.4.1.2011.6.3.3.2.1.1",
    "HUAWEI-DEVICE-MIB::hwSlotType": "1.3.6.1.4.1.2011.6.3.3.2.1.2",
    "HUAWEI-DEVICE-MIB::hwSlotDesc": "1.3.6.1.4.1.2011.6.3.3.2.1.3",
    "HUAWEI-DEVICE-MIB::hwSlotPcbVersion": "1.3.6.1.4.1.2011.6.3.3.2.1.4",
    "HUAWEI-DEVICE-MIB::hwSlotVersion": "1.3.6.1.4.1.2011.6.3.3.2.1.5",
    "HUAWEI-DEVICE-MIB::hwSlotWorkMode": "1.3.6.1.4.1.2011.6.3.3.2.1.6",
    "HUAWEI-DEVICE-MIB::hwSubSlots": "1.3.6.1.4.1.2011.6.3.3.2.1.7",
    "HUAWEI-DEVICE-MIB::hwSlotOperStatus": "1.3.6.1.4.1.2011.6.3.3.2.1.8",
    "HUAWEI-DEVICE-MIB::hwSlotAdminStatus": "1.3.6.1.4.1.2011.6.3.3.2.1.9",
    "HUAWEI-DEVICE-MIB::hwSlotRowStatus": "1.3.6.1.4.1.2011.6.3.3.2.1.10",
    "HUAWEI-DEVICE-MIB::hwSlotPhySerialNum": "1.3.6.1.4.1.2011.6.3.3.2.1.11",
    "HUAWEI-DEVICE-MIB::hwSubslotTable": "1.3.6.1.4.1.2011.6.3.3.3",
    "HUAWEI-DEVICE-MIB::hwSubslotEntry": "1.3.6.1.4.1.2011.6.3.3.3.1",
    "HUAWEI-DEVICE-MIB::hwSubslotIndex": "1.3.6.1.4.1.2011.6.3.3.3.1.1",
    "HUAWEI-DEVICE-MIB::hwSubslotType": "1.3.6.1.4.1.2011.6.3.3.3.1.2",
    "HUAWEI-DEVICE-MIB::hwSubslotPorts": "1.3.6.1.4.1.2011.6.3.3.3.1.3",
    "HUAWEI-DEVICE-MIB::hwSubslotOperStatus": "1.3.6.1.4.1.2011.6.3.3.3.1.5",
    "HUAWEI-DEVICE-MIB::hwSubslotAdminStatus": "1.3.6.1.4.1.2011.6.3.3.3.1.7",
    "HUAWEI-DEVICE-MIB::hwSubslotVersion": "1.3.6.1.4.1.2011.6.3.3.3.1.8",
    "HUAWEI-DEVICE-MIB::hwSubSlotDesc": "1.3.6.1.4.1.2011.6.3.3.3.1.9",
    "HUAWEI-DEVICE-MIB::hwSubslotRowStatus": "1.3.6.1.4.1.2011.6.3.3.3.1.10",
    "HUAWEI-DEVICE-MIB::hwPortTable": "1.3.6.1.4.1.2011.6.3.3.4",
    "HUAWEI-DEVICE-MIB::hwPortEntry": "1.3.6.1.4.1.2011.6.3.3.4.1",
    "HUAWEI-DEVICE-MIB::hwPortIndex": "1.3.6.1.4.1.2011.6.3.3.4.1.1",
    "HUAWEI-DEVICE-MIB::hwPortType": "1.3.6.1.4.1.2011.6.3.3.4.1.2",
    "HUAWEI-DEVICE-MIB::hwPortDesc": "1.3.6.1.4.1.2011.6.3.3.4.1.3",
    "HUAWEI-DEVICE-MIB::hwPortSpeed": "1.3.6.1.4.1.2011.6.3.3.4.1.4",
    "HUAWEI-DEVICE-MIB::hwPortOperStatus": "1.3.6.1.4.1.2011.6.3.3.4.1.5",
    "HUAWEI-DEVICE-MIB::hwPortAdminStatus": "1.3.6.1.4.1.2011.6.3.3.4.1.6",
    "HUAWEI-DEVICE-MIB::hwFrameLinks": "1.3.6.1.4.1.2011.6.3.3.5",
    "HUAWEI-DEVICE-MIB::hwFrameLinkNumber": "1.3.6.1.4.1.2011.6.3.3.5.1",
    "HUAWEI-DEVICE-MIB::hwFrameLinkTable": "1.3.6.1.4.1.2011.6.3.3.5.2",
    "HUAWEI-DEVICE-MIB::hwFrameLinkEntry": "1.3.6.1.4.1.2011.6.3.3.5.2.1",
    "HUAWEI-DEVICE-MIB::hwFrameLinkIndex": "1.3.6.1.4.1.2011.6.3.3.5.2.1.1",
    "HUAWEI-DEVICE-MIB::hwFrameLinkLeftFrame": "1.3.6.1.4.1.2011.6.3.3.5.2.1.2",
    "HUAWEI-DEVICE-MIB::hwFrameLinkLeftSlot": "1.3.6.1.4.1.2011.6.3.3.5.2.1.3",
    "HUAWEI-DEVICE-MIB::hwFrameLinkLeftSubSlot": "1.3.6.1.4.1.2011.6.3.3.5.2.1.4",
    "HUAWEI-DEVICE-MIB::hwFrameLinkLeftPort": "1.3.6.1.4.1.2011.6.3.3.5.2.1.5",
    "HUAWEI-DEVICE-MIB::hwFrameLinkRightFrame": "1.3.6.1.4.1.2011.6.3.3.5.2.1.6",
    "HUAWEI-DEVICE-MIB::hwFrameLinkRightSlot": "1.3.6.1.4.1.2011.6.3.3.5.2.1.7",
    "HUAWEI-DEVICE-MIB::hwFrameLinkRightSubSlot": "1.3.6.1.4.1.2011.6.3.3.5.2.1.8",
    "HUAWEI-DEVICE-MIB::hwFrameLinkRightPort": "1.3.6.1.4.1.2011.6.3.3.5.2.1.9",
    "HUAWEI-DEVICE-MIB::hwFrameLinkOperStatus": "1.3.6.1.4.1.2011.6.3.3.5.2.1.10",
    "HUAWEI-DEVICE-MIB::hwFrameLinkRowStatus": "1.3.6.1.4.1.2011.6.3.3.5.2.1.11",
    "HUAWEI-DEVICE-MIB::hwFrameLinkNextIndex": "1.3.6.1.4.1.2011.6.3.3.5.3",
    "HUAWEI-DEVICE-MIB::hwNarrowBoard": "1.3.6.1.4.1.2011.6.3.3.6",
    "HUAWEI-DEVICE-MIB::hwBoardAttrTable": "1.3.6.1.4.1.2011.6.3.3.6.1",
    "HUAWEI-DEVICE-MIB::hwBoardAttrEntry": "1.3.6.1.4.1.2011.6.3.3.6.1.1",
    "HUAWEI-DEVICE-MIB::hwBoardAulaw": "1.3.6.1.4.1.2011.6.3.3.6.1.1.1",
    "HUAWEI-DEVICE-MIB::hwBoardCurrent": "1.3.6.1.4.1.2011.6.3.3.6.1.1.2",
    "HUAWEI-DEVICE-MIB::hwBoardImpedance": "1.3.6.1.4.1.2011.6.3.3.6.1.1.3",
    "HUAWEI-DEVICE-MIB::hwCpuDevTable": "1.3.6.1.4.1.2011.6.3.4",
    "HUAWEI-DEVICE-MIB::hwCpuDevEntry": "1.3.6.1.4.1.2011.6.3.4.1",
    "HUAWEI-DEVICE-MIB::hwCpuDevIndex": "1.3.6.1.4.1.2011.6.3.4.1.1",
    "HUAWEI-DEVICE-MIB::hwCpuDevDuty": "1.3.6.1.4.1.2011.6.3.4.1.2",
    "HUAWEI-DEVICE-MIB::hwAvgDuty1min": "1.3.6.1.4.1.2011.6.3.4.1.3",
    "HUAWEI-DEVICE-MIB::hwAvgDuty5min": "1.3.6.1.4.1.2011.6.3.4.1.4",
    "HUAWEI-DEVICE-MIB::hwMemoryDev": "1.3.6.1.4.1.2011.6.3.5",
    "HUAWEI-DEVICE-MIB::hwMemoryDevTable": "1.3.6.1.4.1.2011.6.3.5.1",
    "HUAWEI-DEVICE-MIB::hwMemoryDevEntry": "1.3.6.1.4.1.2011.6.3.5.1.1",
    "HUAWEI-DEVICE-MIB::hwMemoryDevModuleIndex": "1.3.6.1.4.1.2011.6.3.5.1.1.1",
    "HUAWEI-DEVICE-MIB::hwMemoryDevSize": "1.3.6.1.4.1.2011.6.3.5.1.1.2",
    "HUAWEI-DEVICE-MIB::hwMemoryDevFree": "1.3.6.1.4.1.2011.6.3.5.1.1.3",
    "HUAWEI-DEVICE-MIB::hwMemoryDevRawSliceUsed": "1.3.6.1.4.1.2011.6.3.5.1.1.4",
    "HUAWEI-DEVICE-MIB::hwMemoryDevLargestFree": "1.3.6.1.4.1.2011.6.3.5.1.1.5",
    "HUAWEI-DEVICE-MIB::hwMemoryDevFail": "1.3.6.1.4.1.2011.6.3.5.1.1.6",
    "HUAWEI-DEVICE-MIB::hwMemoryDevFailNoMem": "1.3.6.1.4.1.2011.6.3.5.1.1.7",
    "HUAWEI-DEVICE-MIB::hwBufferTable": "1.3.6.1.4.1.2011.6.3.5.2",
    "HUAWEI-DEVICE-MIB::hwBufferEntry": "1.3.6.1.4.1.2011.6.3.5.2.1",
    "HUAWEI-DEVICE-MIB::hwBufferModuleIndex": "1.3.6.1.4.1.2011.6.3.5.2.1.1",
    "HUAWEI-DEVICE-MIB::hwBufferSize": "1.3.6.1.4.1.2011.6.3.5.2.1.2",
    "HUAWEI-DEVICE-MIB::hwBufferCurrentTotal": "1.3.6.1.4.1.2011.6.3.5.2.1.3",
    "HUAWEI-DEVICE-MIB::hwBufferCurrentUsed": "1.3.6.1.4.1.2011.6.3.5.2.1.4",
    "HUAWEI-DEVICE-MIB::hwFlashDev": "1.3.6.1.4.1.2011.6.3.6",
    "HUAWEI-DEVICE-MIB::hwFlashDevTable": "1.3.6.1.4.1.2011.6.3.6.1",
    "HUAWEI-DEVICE-MIB::hwFlashDevEntry": "1.3.6.1.4.1.2011.6.3.6.1.1",
    "HUAWEI-DEVICE-MIB::hwFlashDevIndex": "1.3.6.1.4.1.2011.6.3.6.1.1.1",
    "HUAWEI-DEVICE-MIB::hwFlashDevSize": "1.3.6.1.4.1.2011.6.3.6.1.1.2",
    "HUAWEI-DEVICE-MIB::hwFlashDevFree": "1.3.6.1.4.1.2011.6.3.6.1.1.3",
    "HUAWEI-DEVICE-MIB::hwFlashDevEraseTime": "1.3.6.1.4.1.2011.6.3.6.1.1.4",
    "HUAWEI-DEVICE-MIB::hwFlashDevEraseStatus": "1.3.6.1.4.1.2011.6.3.6.1.1.5",
    "HUAWEI-DEVICE-MIB::hwFlashDevStatus": "1.3.6.1.4.1.2011.6.3.6.1.1.6",
    "HUAWEI-DEVICE-MIB::hwAlarmInfo": "1.3.6.1.4.1.2011.6.3.7",
    "HUAWEI-DEVICE-MIB::hwAlarmTable": "1.3.6.1.4.1.2011.6.3.7.1",
    "HUAWEI-DEVICE-MIB::hwAlarmEntry": "1.3.6.1.4.1.2011.6.3.7.1.1",
    "HUAWEI-DEVICE-MIB::hwAlarmSerialIndex": "1.3.6.1.4.1.2011.6.3.7.1.1.1",
    "HUAWEI-DEVICE-MIB::hwAlarmType": "1.3.6.1.4.1.2011.6.3.7.1.1.2",
    "HUAWEI-DEVICE-MIB::hwAlarmOcurTime": "1.3.6.1.4.1.2011.6.3.7.1.1.3",
    "HUAWEI-DEVICE-MIB::trapObjectIdValue": "1.3.6.1.4.1.2011.6.3.7.1.1.4",
    "HUAWEI-DEVICE-MIB::hwDevTraps": "1.3.6.1.4.1.2011.6.3.8",
    "HUAWEI-DEVICE-MIB::hwDevTrapVbOids": "1.3.6.1.4.1.2011.6.3.8.1",
    "HUAWEI-DEVICE-MIB::hwFrameAdminResult": "1.3.6.1.4.1.2011.6.3.8.1.1",
    "HUAWEI-DEVICE-MIB::hwSlotAdminResult": "1.3.6.1.4.1.2011.6.3.8.1.2",
    "HUAWEI-DEVICE-MIB::hwSubslotAdminResult": "1.3.6.1.4.1.2011.6.3.8.1.3",
    "HUAWEI-DEVICE-MIB::hwPortAdminResult": "1.3.6.1.4.1.2011.6.3.8.1.4",
    "HUAWEI-DEVICE-MIB::hwDevGeneralTraps": "1.3.6.1.4.1.2011.6.3.8.5.0",
    "HUAWEI-DEVICE-MIB::hwFrameAdminResultTrap": "1.3.6.1.4.1.2011.6.3.8.5.0.1",
    "HUAWEI-DEVICE-MIB::hwSlotAdminResultTrap": "1.3.6.1.4.1.2011.6.3.8.5.0.2",
    "HUAWEI-DEVICE-MIB::hwSubSlotAdminResultTrap": "1.3.6.1.4.1.2011.6.3.8.5.0.3",
    "HUAWEI-DEVICE-MIB::hwPortAdminResultTrap": "1.3.6.1.4.1.2011.6.3.8.5.0.4",
    "HUAWEI-DEVICE-MIB::hwCliUserMgmt": "1.3.6.1.4.1.2011.6.3.10",
    "HUAWEI-DEVICE-MIB::hwCliUserParaTable": "1.3.6.1.4.1.2011.6.3.10.1",
    "HUAWEI-DEVICE-MIB::hwCliUserParaEntry": "1.3.6.1.4.1.2011.6.3.10.1.1",
    "HUAWEI-DEVICE-MIB::hwCliUserName": "1.3.6.1.4.1.2011.6.3.10.1.1.1",
    "HUAWEI-DEVICE-MIB::hwCliUserPassword": "1.3.6.1.4.1.2011.6.3.10.1.1.2",
    "HUAWEI-DEVICE-MIB::hwCliUserLevel": "1.3.6.1.4.1.2011.6.3.10.1.1.3",
    "HUAWEI-DEVICE-MIB::hwCliUserLogins": "1.3.6.1.4.1.2011.6.3.10.1.1.4",
    "HUAWEI-DEVICE-MIB::hwCliUserDecr": "1.3.6.1.4.1.2011.6.3.10.1.1.5",
    "HUAWEI-DEVICE-MIB::hwCliUserRowStatus": "1.3.6.1.4.1.2011.6.3.10.1.1.6",
    "HUAWEI-DEVICE-MIB::hwCliClientTable": "1.3.6.1.4.1.2011.6.3.10.2",
    "HUAWEI-DEVICE-MIB::hwCliClientEntry": "1.3.6.1.4.1.2011.6.3.10.2.1",
    "HUAWEI-DEVICE-MIB::hwCliClientID": "1.3.6.1.4.1.2011.6.3.10.2.1.1",
    "HUAWEI-DEVICE-MIB::hwCliClientUserName": "1.3.6.1.4.1.2011.6.3.10.2.1.2",
    "HUAWEI-DEVICE-MIB::hwCliClientType": "1.3.6.1.4.1.2011.6.3.10.2.1.3",
    "HUAWEI-DEVICE-MIB::hwCliClientIp": "1.3.6.1.4.1.2011.6.3.10.2.1.4",
    "HUAWEI-DEVICE-MIB::hwCliClientLoginTime": "1.3.6.1.4.1.2011.6.3.10.2.1.5",
    "HUAWEI-DEVICE-MIB::hwCliClientAdminStatus": "1.3.6.1.4.1.2011.6.3.10.2.1.6",
    "HUAWEI-DEVICE-MIB::hwDevCompatibleTable": "1.3.6.1.4.1.2011.6.3.11",
    "HUAWEI-DEVICE-MIB::hwCompatibleSysOid": "1.3.6.1.4.1.2011.6.3.11.1",
    "HUAWEI-DEVICE-MIB::hwCompatibleVersion": "1.3.6.1.4.1.2011.6.3.11.2",
    "HUAWEI-DEVICE-MIB::hwCompatibleVRCB": "1.3.6.1.4.1.2011.6.3.11.3",
    "HUAWEI-DEVICE-MIB::hwCompatibleProductName": "1.3.6.1.4.1.2011.6.3.11.4",
}

DISPLAY_HINTS = {
    "1.3.6.1.4.1.2011.6.3.1.4": (
        "OctetString",
        "2d-1d-1d,1d:1d:1d.1d,1a1d:1d",
    ),  # HUAWEI-DEVICE-MIB::hwSysTime
    "1.3.6.1.4.1.2011.6.3.7.1.1.3": (
        "OctetString",
        "2d-1d-1d,1d:1d:1d.1d,1a1d:1d",
    ),  # HUAWEI-DEVICE-MIB::hwAlarmOcurTime
    "1.3.6.1.4.1.2011.6.3.10.2.1.5": (
        "OctetString",
        "2d-1d-1d,1d:1d:1d.1d,1a1d:1d",
    ),  # HUAWEI-DEVICE-MIB::hwCliClientLoginTime
}

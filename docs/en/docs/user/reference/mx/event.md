# event MX Message

`event` message is generated by [classifier](../../../admin/reference/services/classifier.md)
service when create Event.

## Message Headers

Message-Type
: Type of message. Always `event`.

Sharding-Key
: Key for consistent sharding.

Labels
: Managed Object's effective labels.

## Message Format

Message contains JSON object, containing objects of following structure

| Name       | Type     | Description                                                          |
| ---------- | -------- | -------------------------------------------------------------------- |
| timestamp                       | DateTime             | ISO 8601 timestamp (i.e. `YYYY-MM-DDTHH:MM:SS`) of register source message    |
| message_id                      | String               | Global message identifier                                                     |
| collector_type                  | String               | Event source (collector) `syslog/snmptrap/system`                             |
| collector                       | String               | Source collector Pool                                                         |
| address                         | String               | SNMP Trap Source Address                                                      |
| managed_object                  | Object {{ complex }} | Managed Object details                                                        |
| {{ tab }} id                    | String               | Managed Object's ID                                                           |
| {{ tab }} remote_system         | Object {{ complex }} | Source [remote system](../concepts/remote-system/index.md) for Managed Object |
| {{ tab2 }} id                   | String               | External system's id                                                          |
| {{ tab2 }} name                 | String               | External system's name                                                        |
| {{ tab }} name                  | String               | Managed Object's name                                                         |
| {{ tab }} remote_id             | String               | External system's id (Opaque attribbute)                                      |
| {{ tab }} bi_id                 | Integer              | Managed Object's BI ID                                                        |
| {{ tab }} administrative_domain | Object {{ complex }} | Administrative Domain details                                                 |
| {{ tab2 }} id                   | String               | Administrative Domain's ID                                                    |
| {{ tab2 }} name                 | String               | Administrative Domain's name                                                  |
| {{ tab2 }} remote_id            | String               | Managed Object Administrative Domain's ID in Remote System (if any)            |
| {{ tab2 }} remote_system        | Object {{ complex }} | Source [remote system](../concepts/remote-system/index.md) for Managed Object Administrative Domain |
| {{ tab4 }} id                   | String               | External system's id                                                           |
| {{ tab4 }} name                 | String               | External system's name                                                         |
| {{ tab }} labels                | Array of String      | Managed Object's labels                                                        |
| event_class                     | String               | Event Class (set by Classifier)                                                |
| {{ tab }} id                    | String               | Event Class's ID                                                               |
| {{ tab }} name                  | String               | Event Class's Name                                                             |
| event_vars                      | Object {{ complex }} | Key-value dictionary of event's variables                                      |
| data (syslog)                   | Object {{ complex }} | Syslog message body content                                                    |
| {{ tab }} facility              | String               | Syslog facility                                                                |
| {{ tab }} severity              | String               | Syslog severity                                                                |
| {{ tab }} message               | String               | Syslog message                                                                 |
| data (snmptrap)                 | Object {{ complex }} | SNMP Trap message VarBinds                                                     |
| {{ tab }} vars                  | Array of {{ complex }} | SNMP Trap varbinds              |
| {{ tab2 }} oid                  | String               | SNMP var OID                                                                   |
| {{ tab2 }} resolved_oid         | String               | Resolved SNMP Var OID                                                          |
| {{ tab2 }} value                | String               | SNMP Var value                                                                 |
| {{ tab2 }} resolved_value       | String               | Resolved (with hints) SNMP Var value                                           |


## Example

```json
{
  "timestamp": "2022-07-23T19:04:52",
  "message_id": "2075b637-3a6c-4e09-b7b6-2f6ac63f68bb",
  "collector_type": "snmptrap",
  "collector": "default",
  "address": "127.0.0.1",
  "managed_object": {
    "id": "450",
    "bi_id": 7602684790455147111,
    "name": "device-1",
    "administrative_domain": {
      "id": 11,
      "name": "default",
      "remote_system": {
        "id": "596e715fc165cf1e082ea14c",
        "name": "TEST"
      },
      "remote_id": "1"
    },
    "labels": [],
    "remote_system": {
      "id": "596e715fc165cf1e082ea14c",
      "name": "TEST"
    },
    "remote_id": "22"
  },
  "event_class": {
    "id": "5ec11167c8e0399ae0e05eb1",
    "name": "Chassis | CPU | CPU Rate Limit"
  },
  "event_vars": {
    "cpu": "32",
    "traffic": "mcRouting"
  },
  "data": {
    "vars": [
      {
        "oid": "1.3.6.1.2.1.1.3.0",
        "value": "402494183",
        "resolved_oid": "DISMAN-EVENT-MIB::sysUpTimeInstance",
        "resolved_value": "402494183"
      },
      {
        "oid": "1.3.6.1.6.3.1.1.4.1.0",
        "value": "1.3.6.1.4.1.35265.1.23.1.773.1.0.1",
        "resolved_oid": "SNMPv2-MIB::snmpTrapOID.0",
        "resolved_value": "ELTEX-MES-SWITCH-RATE-LIMITER-MIB::eltCpuRateLimiterTrap"
      },
      {
        "oid": "1.3.6.1.4.1.35265.1.23.1.773.1.1.1.1.1.22",
        "value": "22",
        "resolved_oid": "ELTEX-MES-SWITCH-RATE-LIMITER-MIB::eltCpuRateLimiterIndex.22",
        "resolved_value": "mcRouting"
      },
      {
        "oid": "1.3.6.1.4.1.35265.1.23.1.773.1.1.1.1.2.22",
        "value": "32",
        "resolved_oid": "ELTEX-MES-SWITCH-RATE-LIMITER-MIB::eltCpuRateLimiterValue.22",
        "resolved_value": "32"
      }
    ]
  }
}
```
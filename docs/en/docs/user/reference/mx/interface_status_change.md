# Interface Status Change MX Message

`interface_status_change` message is generated by [Interface Status Discovery](../../../admin/reference/discovery/periodic/interfacestatus.md)
service when create Event.

## Message Headers

Message-Type
: Type of message. Always `interface_status_change`.

Sharding-Key
: Key for consistent sharding.

Labels
: Managed Object's effective labels.

## Message Format

Message contains JSON object, containing objects of following structure


| Name       | Type     | Description                                                          |
| ---------- | -------- | -------------------------------------------------------------------- |
| name                            | String               | Interface name                             |
| description                     | String               | Interface description                      |
| status                          | Bool                 | Interface oper status                      |
| managed_object                  | Object {{ complex }} | Managed Object details                     |
| {{ tab }} id                    | String               | Managed Object's ID                        |
| {{ tab }} name                  | String               | Managed Object's Name                      |
| {{ tab }} description           | String               | Managed Object's Description               |
| {{ tab }} address               | String               | Managed Object's Address                   |
| {{ tab }} administrative_domain | Object {{ complex }} | Administrative Domain details              |
| {{ tab2 }} id                   | String               | Administrative Domain's ID                 |
| {{ tab2 }} name                 | String               | Administrative Domain's name               |
| {{ tab }} profile               | Object {{ complex }} | SA Profile details                         |
| {{ tab2 }} id                   | String               | SA Profile's ID                            |
| {{ tab2 }} name                 | String               | SA Profile's name                          |


## Example

```json
{
  "name": "Gi 1/0/3",
  "description": "<< User port 1 >>",
  "status": false,
  "managed_object": {
    "id": 1111,
    "name": "device2",
    "description": null,
    "address": "10.10.10.1",
    "profile": {
      "name": "Eltex.MES"
    },
    "administrative_domain": {
      "name": "default"
    }
  }
}
```

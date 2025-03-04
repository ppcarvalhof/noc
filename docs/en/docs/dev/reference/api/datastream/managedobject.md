# managedobject DataStream

`managedobject` [DataStream](index.md) contains summarized [Managed Object](../../../../user/reference/concepts/managed-object/index.md)
state, including capabilities, interfaces and topology

## Fields

| Name                           | Type                          | Description                                                                                        |
| ------------------------------ |-------------------------------|----------------------------------------------------------------------------------------------------|
| id                             | String                        | [Managed Object's](../../../../user/reference/concepts/managed-object/index.md) id                 |
| change_id                      | String                        | [Record's Change Id](index.md#change-id)                                                           |
| remote_system                  | Object {{ complex }}          | Source [remote system](../../../../user/reference/concepts/remote-system/index.md) for object      |
| {{ tab }} id                   | String                        | External system's id                                                                               |
| {{ tab }} name                 | String                        | External system's name                                                                             |
| remote_id                      | String                        | External system's id (Opaque attribbute)                                                           |
| bi_id                          | Integer                       | BI Database id (metrics)                                                                           |
| name                           | String                        | Object's name                                                                                      |
| profile                        | String                        | [SA Profile](../../../../user/reference/concepts/sa-profile/index.md)                              |
| vendor                         | String                        | Vendor                                                                                             |
| platform                       | String                        | Platform                                                                                           |
| version                        | String                        | Firmware version                                                                                   |
| address                        | String                        | Management Address                                                                                 |
| description                    | String                        | Managed Object description                                                                         |
| tags                           | Array of String               | Managed Object tags                                                                                |
| is_managed                     | Boolean                       | Object is managed                                                                                  |
| object_profile                 | Object {{ complex }}          | [Managed Object Profile's data](../../../../user/reference/concepts/managed-object/index.md#level) |
| {{ tab }} id                   | String                        | Profile's ID                                                                                       |
| {{ tab }} name                 | String                        | Profile's Name                                                                                     |
| {{ tab }} level                | Integer                       | Managed Object's [level](../../../../user/reference/concepts/managed-object-profile/index.md)      |
| {{ tab }} enable_ping          | Boolean                       | Ping probe is enabled                                                                              |
| {{ tab }} enable_box           | Boolean                       | [Box discovery](../../../../admin/reference/discovery/box/index.md) is enabled                     |
| {{ tab }} enable_periodic      | Boolean                       | [Periodic discovery](../../../../admin/reference/discovery/periodic/index.md) is enabled           |
| {{ tab }} tags                 | Array of String               | Managed Object Profile tags                                                                        |
| config                         | Object {{ complex }}          | Optional Object's config metadata (if any)                                                         |
| {{ tab }} revision             | String                        | Config revision ID                                                                                 |
| {{ tab }} size                 | Integer                       | Config size in octets                                                                              |
| {{ tab }} updated              | String                        | Last modification timestamp in ISO 8601 format                                                     |
| capabilities                   | Array of Object {{ complex }} | List of object's [capabilities](#caps)                                                             |
| {{ tab }} name                 | String                        | Capability's name                                                                                  |
| {{ tab }} value                | String                        | Capabbility's value                                                                                |
| service_groups                 | Array of Object {{ complex }} | Service [Resource Groups](../../../../user/reference/concepts/resource-group/index.md)             |
| {{ tab }} id                   | String                        | [Resource Group's](../../../../user/reference/concepts/resource-group/index.md) id                 |
| {{ tab }} name                 | String                        | [Resource Group's](../../../../user/reference/concepts/resource-group/index.md) id                 |
| {{ tab }} technology           | String                        | [Technology's](../../../../user/reference/concepts/technology/index.md) name                       |
| {{ tab }} static               | Boolean                       | true if group is static                                                                            |
| client_groups                  | Array of Object {{ complex }} | Client [Resource Groups](../../../../user/reference/concepts/resource-group/index.md)              |
| {{ tab }} id                   | String                        | [Resource Group's](../../../../user/reference/concepts/resource-group/index.md) id                 |
| {{ tab }} name                 | String                        | [Resource Group's](../../../../user/reference/concepts/resource-group/index.md) id                 |
| {{ tab }} technology           | String                        | [Technology's](../../../../user/reference/concepts/technology/index.md) name                       |
| {{ tab }} static               | Boolean                       | true if group is static                                                                            |
| forwarding-instances           | Array of Object {{ complex }} | List of VPNs and virtual tables                                                                    |
| {{ tab }} name                 | String                        | Forwarding instance name                                                                           |
| {{ tab }} type                 | String                        | Forwarding instance type. One of:                                                                  |
|                                |                               | table, bridge, vrf, vll, vpls, evpn, vxlan                                                         |
| {{ tab }} rd                   | String                        | VPN route-distinguisher                                                                            |
| {{ tab }} vpn_id               | String                        | Globally-unique VPN id                                                                             |
| {{ tab }} rt_export            | Array of String               | List of exported route-targets                                                                     |
| {{ tab }} rt_import            | Array of String               | List of imported route-targets                                                                     |
| {{ tab }} subinterfaces        | Array of String               | List of subinterfaces in given forwarding instance                                                 |
| interfaces                     | Array of Object {{ complex }} | List of physical interfaces                                                                        |
| {{ tab }} name                 | String                        | Interface's name (Normalized by profile)                                                           |
| {{ tab }} type                 | String                        | Interface's type                                                                                   |
| {{ tab }} admin_status         | Boolean                       | Administrative status of interface                                                                 |
| {{ tab }} enabled_protocols    | Array of String               | List of active protocols                                                                           |
| {{ tab }} description          | String                        | Description                                                                                        |
| {{ tab }} hints                | Array of String               | List of optional hints, like `uni`, `nni`                                                          |
| {{ tab }} snmp_ifindex         | Integer                       | SNMP ifIndex                                                                                       |
| {{ tab }} mac                  | String                        | MAC-address                                                                                        |
| {{ tab }} aggregated_interface | String                        | LAG interfacename (for LAG members)                                                                |
| {{ tab }} subinterfaces        | Array of Object {{ complex }} | List of logical interfaces                                                                         |
| {{ tab2 }} name                | String                        | Subinterface name (Normalized by profile)                                                          |
| {{ tab2 }} description         | String                        | Description                                                                                        |
| {{ tab2 }} mac                 | String                        | MAC-address                                                                                        |
| {{ tab2 }} enabled_afi         | Array of String               | Active address families                                                                            |
| {{ tab2 }} ipv4_addresses      | Array of String               | List of IPv4 addresses                                                                             |
| {{ tab2 }} ipv6_addresses      | Array of String               | List of IPv6 addresses                                                                             |
| {{ tab2 }} iso_addresses       | Array of String               | List of ISO/CLNS addresses                                                                         |
| {{ tab2 }} vpi                 | Integer                       | ATM VPI                                                                                            |
| {{ tab2 }} vci                 | Integer                       | ATM VCI                                                                                            |
| {{ tab2 }} enabled_protocols   | Array of String               | Enabled protocols                                                                                  |
| {{ tab2 }} snmp_ifindex        | Integer                       | SNMP ifIndex                                                                                       |
| {{ tab2 }} untagged_vlan       | Integer                       | Untagged VLAN (for BRIDGE)                                                                         |
| {{ tab2 }} tagged_vlan         | Array of Integer              | List of tagged VLANs (for BRIDGE)                                                                  |
| {{ tab2 }} vlan_ids            | Array of Integer              | Stack of VLANs for L3 interfaces                                                                   |
| {{ tab }} link                 | Array of Object {{ complex }} | List of links                                                                                      |
| {{ tab2 }} object              | Integer                       | Remote object\'s ID                                                                                |
| {{ tab2 }} interface           | String                        | Remote port's name (interfaces.name)                                                               |
| {{ tab2 }} method              | String                        | Discovery method                                                                                   |
| {{ tab2 }} is_uplink           | Boolean                       | True, if link is uplink                                                                            |
| {{ tab }} services             | Array of Object {{ complex }} | Services related to the port                                                                       |
| {{ tab2 }} id                  | String                        | Service\'s ID                                                                                      |
| {{ tab2 }} remote_system       | Object                        | Source [remote system](../../../../user/reference/concepts/remote-system/index.md) for service     |
| {{ tab3 }} id                  | String                        | External system's id                                                                               |
| {{ tab3 }} name                | String                        | External system's name                                                                             |
| {{ tab2 }} remote_id           | String                        | Service id in External system (Opaque attribute)                                                   |
| asset                          | Array of Object {{ complex }} | Hardware configuration/Inventory data                                                              |
| {{ tab }} id                   | String                        | Inventory object\'s ID                                                                             |
| {{ tab }} model                | Object {{ complex }}          | Inventory model (Object model)                                                                     |
| {{ tab2 }} id                  | String                        | Inventory model\'s ID                                                                              |
| {{ tab2 }} name                | String                        | Inventory model\'s name                                                                            |
| {{ tab2 }} tags                | Array of String               | [Object model's tags](../../../../dev/reference/object-model/tags.md)                              |
| {{ tab2 }} vendor              | Object {{ complex }}          | Inventory model\'s vendor                                                                          |
| {{ tab3 }} id                  | String                        | Vendor\'s ID                                                                                       |
| {{ tab3 }} name                | String                        | Vendor\'s Name                                                                                     |
| {{ tab }} serial               | String                        | Inventory object's serial number                                                                   |
| {{ tab }} part_no              | Array of String               | Inventory object's Part Numbers                                                                    |
| {{ tab }} order_part_no        | Array of String               | Inventory object's Order Part Numbers                                                              |
| {{ tab }} revision             | String                        | Inventory object's hardware revision                                                               |
| {{ tab }} data                 | Object {{ complex }}          | Attached data (see `Model Interfaces`)                                                             |
| {{ tab }} slots                | Array of Object {{ complex }} | Object's slots configuration                                                                       |
| {{ tab2 }} name                | String                        | Name of slot                                                                                       |
| {{ tab2 }} direction           | String                        | Slot's direction:                                                                                  |
|                                |                               |                                                                                                    |
|                                |                               | &bull; i - inner (nested object)                                                                   |
|                                |                               | &bull; s - same level (horizontal connection)                                                      |
| {{ tab2 }} protocols           | Array of String               | List of protocols, supported by slot                                                               |
|                                |                               | (see [Inventory Protocols](../../../../dev/reference/inventory-protocols.md))                      |
| {{ tab2 }} interface           | String                        | Optional interface name related to the slot                                                        |
| {{ tab2 }} slots               | Array of Object {{ complex }} | List of inner slots for `i` direction, same structure as `slots`                                   |

## Filters

### pool(name)

Restrict stream to objects belonging to pool `name`

name
: Pool name

## Access

[API Key](../../../../user/reference/concepts/apikey/index.md) with `datastream:managedobject` permissions
required.

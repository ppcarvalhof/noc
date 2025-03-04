---
tags:
  - reference
---
# alarm DataStream

`alarm` [DataStream](index.md) contains summarized alarms state

## Fields

| Name                      | Type                 | Description                                                                                        |
| ------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| id                        | String               | Alarm Id                                                                                           |
| timestamp                 | String               | ISO 8601 timestamp (i.e. YYYY-MM-DDTHH:MM:SS) of alarm rising                                      |
| clear_timestamp           | String               | ISO 8601 timestamp (i.e. YYYY-MM-DDTHH:MM:SS) of alarm clearange (for closed alarms only)          |
| severity                  | Integer              | Alarm severity                                                                                     |
| root                      | String               | ID of root alarm (for consequences only)                                                           |
| object                    | Object {{ complex }} | Managed Object                                                                                     |
| {{ tab }} id              | String               | Managed Object's ID                                                                                |
| {{ tab }} object_profile  | Object {{ complex }} | Managed Object Profile                                                                             |
| {{ tab2 }} id             | String               | Managed Object Profile's ID                                                                        |
| {{ tab2 }} name           | String               | Managed Object Profile's Name                                                                      |
| {{ tab }} remote_system   | Object {{ complex }} | Managed Object's [Remote System](../../../user/reference/concepts/remote-system/index.md) (if imported) |
| {{ tab2 }} id             | String               | Remote System's ID                                                                                 |
| {{ tab2 }} name           | String               | Remote System's Name                                                                               |
| {{ tab }} remote_id       | String               | Managed Object's ID in Remote System (if any)                                                      |
| alarm_class               | String               | Alarm Class                                                                                        |
| {{ tab }} id              | String               | Alarm Class' ID                                                                                    |
| {{ tab }} name            | String               | Alarm Class' Name                                                                                  |
| vars                      | Object {{ complex }} | Key-value dictionary of alarm's variables                                                          |
| reopens                   | Integer              | Number of alarm's reopens                                                                          |
| tags                      | Object {{ complex }} | Alarm tags                                                                                         |
| escalation                | Object {{ complex }} | Escalation data (if escalated)                                                                     |
| {{ tab }} timestamp       | String               | Escalation timestamp in ISO 8601 format                                                            |
| {{ tab }} tt_system       | Object {{ complex }} | TT System to escalate                                                                              |
| {{ tab2 }} id             | String               | TT System's ID                                                                                     |
| {{ tab2 }} name           | String               | TT System's name                                                                                   |
| {{ tab }} error           | String               | Escalation error text (if any)                                                                     |
| {{ tab }} tt_id           | String               | TT ID                                                                                              |
| {{ tab }} close_timestamp | String               | Escalation closing timestamp in ISO 8601 format (if closed)                                        |
| {{ tab }} close_error     | String               | Escalation closing error text (if any)                                                             |
| direct_services           | Object {{ complex }} | Summary of services directly affected by alarm                                                     |
| {{ tab }} profile         | Object {{ complex }} | Service Profile                                                                                    |
| {{ tab2 }} id             | String               | Service Profile's ID                                                                               |
| {{ tab2 }} name           | String               | Service Profile's name                                                                             |
| {{ tab }} summary         | Integer              | Number of affected services                                                                        |
| total_services            | Object {{ complex }} | Summary of services directly affected by alarm and all consequences                                |
| {{ tab }} profile         | Object {{ complex }} | Service Profile                                                                                    |
| {{ tab2 }} id             | String               | Service Profile's ID                                                                               |
| {{ tab2 }} name           | String               | Service Profile's name                                                                             |
| {{ tab }} summary         | String               | Number of affected services                                                                        |
| direct_subscribers        | Object {{ complex }} | Summary of subscribers directly affected by alarm                                                  |
| {{ tab }} profile         | Object {{ complex }} | Subscriber Profile                                                                                 |
| {{ tab2 }} id             | String               | Subscriber Profile's ID                                                                            |
| {{ tab2 }} name           | String               | Subscriber Profile's name                                                                          |
| {{ tab }} summary         | Integer              | Subscriber Profile's summary                                                                       |
| total_subscribers         | Object {{ complex }} | Summary of subscribers directly affected by alarm and all consequences                             |
| {{ tab }} profile         | Object {{ complex }} | Subscriber Profile                                                                                 |
| {{ tab2 }} id             | String               | Subscriber Profile's ID                                                                            |
| {{ tab2 }} name           | String               | Subscriber Profile's name                                                                          |
| {{ tab }} summary         | Integer              | Subscriber Profile's summary                                                                       |

## Access

[API Key](../../../user/reference/concepts/apikey/index.md) with `datastream:alarm` permissions
required.

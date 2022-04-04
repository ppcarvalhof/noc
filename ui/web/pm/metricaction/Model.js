//---------------------------------------------------------------------
// pm.metricaction Model
//---------------------------------------------------------------------
// Copyright (C) 2007-2022 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.pm.metricaction.Model");

Ext.define("NOC.pm.metricaction.Model", {
    extend: "Ext.data.Model",
    rest_url: "/pm/metricaction/",

    fields: [
        {
            name: "id",
            type: "string",
            persist: false
        },
        {
            name: "uuid",
            type: "string"
        },
        {
            name: "description",
            type: "string"
        },
        {
            name: "compose_inputs",
            type: "auto"
        },
        {
            name: "compose_function",
            type: "string"
        },
        {
            name: "compose_metric_type",
            type: "string"
        },
        {
            name: "compose_metric_type__label",
            type: "string",
            persist: false
        },
        {
            name: "activation_config",
            type: "auto"
        },
        {
            name: "deactivation_config",
            type: "auto"
        },
        {
            name: "key_function",
            type: "string"
        },
        {
            name: "alarm_config",
            type: "auto"
        },
        {
            name: "is_builtin",
            type: "boolean",
            persist: false
        }
    ]
});

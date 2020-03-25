//---------------------------------------------------------------------
// inv.reportmetricdetail application
//---------------------------------------------------------------------
// Copyright (C) 2007-2020 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.inv.reportmaxmetrics.Application");

Ext.define("NOC.inv.reportmaxmetrics.Application", {
    extend: "NOC.core.Application",
    requires: [
        "NOC.core.ReportControl",
        "NOC.inv.networksegment.TreeCombo",
        "NOC.inv.interfaceprofile.LookupField",
        "NOC.sa.administrativedomain.TreeCombo",
        "NOC.sa.managedobjectprofile.LookupField",
        "NOC.sa.managedobjectselector.LookupField"
    ],

    items: {
        xtype: "report.control",
        url: "/inv/reportmaxmetrics",
        controls: [
            {
                name: "from_date",
                xtype: "datefield",
                startDay: 1,
                fieldLabel: __("From"),
                allowBlank: false,
                format: "d.m.Y",
                margin: 0,
                width: 210
            },
            {
                name: "to_date",
                xtype: "datefield",
                startDay: 1,
                fieldLabel: __("To"),
                allowBlank: false,
                format: "d.m.Y",
                margin: 0,
                width: 210
            },
            {
                name: "segment",
                xtype: "inv.networksegment.TreeCombo",
                fieldLabel: __("Segment"),
                listWidth: 1,
                listAlign: 'left',
                labelAlign: "left",
                width: 500
            },
            {
                name: "administrative_domain",
                xtype: "sa.administrativedomain.TreeCombo",
                fieldLabel: __("By Adm. domain"),
                listWidth: 1,
                listAlign: 'left',
                labelAlign: "left",
                width: 500,
                allowBlank: true
            },
            {
                name: "selector",
                xtype: "sa.managedobjectselector.LookupField",
                fieldLabel: __("By Selector"),
                listWidth: 1,
                listAlign: 'left',
                labelAlign: "left",
                width: 500,
                allowBlank: true
            },
            {
                name: "object_profile",
                xtype: "sa.managedobjectprofile.LookupField",
                fieldLabel: __("By Profile"),
                listWidth: 1,
                listAlign: 'left',
                labelAlign: "left",
                width: 500,
                allowBlank: true
            },
            {
                name: "interface_profile",
                xtype: "inv.interfaceprofile.LookupField",
                fieldLabel: __("By Interface Profile"),
                listWidth: 1,
                listAlign: 'left',
                labelAlign: "left",
                width: 500,
                allowBlank: true
            },
            {
                name: "description",
                xtype: "textfield",
                fieldLabel: __("Filter by Description (REGEXP)"),
                allowBlank: true,
                uiStyle: "large",
                labelWidth: 170
            },
            {
                name: "exclude_zero",
                xtype: "checkboxfield",
                boxLabel: __("Filter interface has zero load"),
                allowBlank: false,
                defaultValue: true
            }
        ],
        storeData: [
            ["id", __("ID"), false],
            ["object_name", __("Object Name"), true],
            ["object_address", __("IP"), true],
            ["object_platform", __("Object Platform"), true],
            ["object_adm_domain", __("Object Administrative domain"), true],
            ["object_segment", __("Object Segment"), false],
            ["object_container", __("Object Geo Address"), false],
            ["iface_name", __("Interface Name"), true],
            ["iface_description", __("Interface Description"), true],
            ["iface_speed", __("Interface Speed"), false],
            ["max_load_in", __("Maximum Load In"), true],
            ["max_load_in_time", __("Maximum Load In Time"), true],
            ["max_load_out", __("Maximum Load Out"), true],
            ["max_load_out_time", __("Maximum Load Out Time"), true],
            ["avg_load_in", __("AVG Load In"), true],
            ["avg_load_out", __("AVG Load Out"), true],
            ["uplink_iface_name", __("Uplink Interface Name"), true],
            ["uplink_iface_description", __("Uplink Interface Description"), true],
            ["uplink_max_load_in", __("Uplink Maximum Load In"), true],
            ["uplink_max_load_in_time", __("Uplink Maximum Load In Time"), true],
            ["uplink_max_load_out", __("Uplink Maximum Load Out"), true],
            ["uplink_max_load_out_time", __("Uplink Maximum Load Out Time"), true],
            ["uplink_avg_load_in", __("Uplink AVG Load In"), true],
            ["uplink_avg_load_out", __("Uplink AVG Load Out"), true],
            ["uplink_iface_speed", __("Uplink Interface Speed"), false]
        ]
    }
});

//---------------------------------------------------------------------
// inv.interfaceprofile application
//---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.inv.interfaceprofile.Application");

Ext.define("NOC.inv.interfaceprofile.Application", {
    extend: "NOC.core.ModelApplication",
    requires: [
        "NOC.core.label.LabelField",
        "NOC.core.ListFormField",
        "NOC.inv.interfaceprofile.Model",
        "NOC.main.style.LookupField",
        "Ext.ux.form.MultiIntervalField",
        "NOC.pm.metrictype.LookupField",
        "NOC.main.remotesystem.LookupField",
        "NOC.main.ref.windowfunction.LookupField",
        "NOC.pm.thresholdprofile.LookupField",
        "NOC.cm.interfacevalidationpolicy.LookupField",
        "NOC.inv.ifdescpatterns.LookupField",
        "NOC.main.handler.LookupField",
        "Ext.ux.form.GridField",
        "NOC.wf.workflow.LookupField"
    ],
    model: "NOC.inv.interfaceprofile.Model",
    search: true,
    rowClassField: "row_class",
    validationModelId: "inv.InterfaceProfile",
    formMinWidth: 800,
    formMaxWidth: 1000,

    initComponent: function() {
        var me = this,
            fieldSetDefaults = {
                xtype: "container",
                padding: 5,
                layout: "form",
                columnWidth: 0.5
            };
        ;

        me.validationSettingsButton = Ext.create("Ext.button.Button", {
            text: __("Validation"),
            glyph: NOC.glyph.file,
            scope: me,
            handler: me.onValidationSettings
        });

        Ext.apply(me, {
                columns: [
                    {
                        text: __("Name"),
                        dataIndex: "name"
                    },
                    {
                        text: __("Match Expression"),
                        dataIndex: "match_expression",
                        width: 400,
                        renderer: function(v, _x) {
                            var labels = [], text;
                            Ext.each(v, function(label) {
                                labels.push(NOC.render.Label({
                                    badges: label.badges,
                                    name: label.name,
                                    description: label.description || "",
                                    bg_color1: label.bg_color1 || 0,
                                    fg_color1: label.fg_color1 || 0,
                                    bg_color2: label.bg_color2 || 0,
                                    fg_color2: label.fg_color2 || 0
                                }));
                            });
                            text = labels.join("");
                            return '<span data-qtitle="Match Expression" ' +
                                'data-qtip="' + text + '">' + text + '</span>';
                        }
                    },
                    {
                        text: __("Link Events"),
                        dataIndex: "link_events",
                        renderer: function(value) {
                            return {
                                "I": "Ignore",
                                "L": "Log",
                                "A": "Raise"
                            }[value];
                        }
                    },
                    {
                        text: __("Style"),
                        dataIndex: "style",
                        renderer: NOC.render.Lookup("style")
                    },
                    {
                        text: __("Policy"),
                        dataIndex: "discovery_policy",
                        renderer: NOC.render.Choices({
                            I: "Ignore",
                            O: "Create new",
                            R: "Replace",
                            C: "Cloud"
                        })
                    },
                    {
                        text: __("MAC"),
                        dataIndex: "mac_discovery_policy",
                        renderer: NOC.render.Choices({
                            e: __("Transit"),
                            d: __("Disable"),
                            m: __("Management VLAN"),
                            i: __("Direct Downlink"),
                            c: __("Chained Downlink"),
                            u: __("Direct Uplink"),
                            C: __("Cloud Downlink")
                        }),
                        width: 50
                    },
                    {
                        text: __("Description"),
                        dataIndex: "description",
                        flex: 1
                    }
                ],
                fields: [
                    {
                        xtype: "fieldset",
                        layout: "column",
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        border: false,
                        items: [
                            {
                                name: "name",
                                xtype: "textfield",
                                fieldLabel: __("Name"),
                                width: 200,
                                allowBlank: false
                            },
                            {
                                name: "bi_id",
                                xtype: "displayfield",
                                fieldLabel: __("BI ID"),
                                allowBlank: true,
                                uiStyle: "medium"
                            },
                            {
                              name: "labels",
                              xtype: "labelfield",
                              fieldLabel: __("Labels"),
                              allowBlank: true,
                              query: {
                                "enable_interface": true
                              }
                            },
                            {
                                name: "description",
                                xtype: "textarea",
                                fieldLabel: __("Description"),
                                allowBlank: true
                            },
                            {
                                name: "style",
                                xtype: "main.style.LookupField",
                                fieldLabel: __("Style"),
                                allowBlank: true
                            },
                            {
                                name: "is_uni",
                                xtype: "checkbox",
                                boxLabel: __("User Interface"),
                                allowBlank: true
                            },
                            {
                                name: "workflow",
                                xtype: "wf.workflow.LookupField",
                                fieldLabel: __("Workflow"),
                                allowBlank: false
                            },
                            {
                                name: "dynamic_classification_policy",
                                xtype: "combobox",
                                fieldLabel: __("Dynamic Classification Policy"),
                                labelWidth: 200,
                                allowBlank: false,
                                queryMode: "local",
                                displayField: "label",
                                valueField: "id",
                                store: {
                                    fields: ["id", "label"],
                                    data: [
                                        {id: "D", label: "Disable"},
                                        {id: "R", label: "By Rule"},
                                    ]
                                },
                                defaultValue: "R",
                                uiStyle: "medium"
                            },
                        ]
                    },
                    {
                        xtype: "fieldset",
                        layout: "column",
                        title: __("FM"),
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        collapsible: true,
                        items: [
                            {
                                name: "link_events",
                                xtype: "combobox",
                                fieldLabel: __("Link Events"),
                                labelWidth: 200,
                                allowBlank: false,
                                queryMode: "local",
                                displayField: "label",
                                valueField: "id",
                                store: {
                                    fields: ["id", "label"],
                                    data: [
                                        {id: "I", label: "Ignore Link Events"},
                                        {
                                            id: "L",
                                            label: "Log events, do not raise alarms"
                                        },
                                        {id: "A", label: "Raise alarms"}
                                    ]
                                },
                                uiStyle: "medium"
                            },
                            {
                                name: "interface_validation_policy",
                                xtype: "cm.interfacevalidationpolicy.LookupField",
                                fieldLabel: __("Validation Policy"),
                                labelWidth: 200,
                                allowBlank: true
                            },
                            {
                                name: "weight",
                                xtype: "numberfield",
                                labelWidth: 200,
                                width: 50,
                                fieldLabel: __("Alarm Weight"),
                                allowBlank: false,
                                uiStyle: "small"
                            },
                            {
                                name: "status_change_notification",
                                xtype: "combobox",
                                fieldLabel: __("Status Change Notification"),
                                allowBlank: true,
                                labelWidth: 200,
                                defaultValue: "d",
                                store: [
                                    ["d", __("Disabled")],
                                    ["e", __("Enable")],
                                ],
                                uiStyle: "medium"
                            },
                            {
                                xtype: "checkbox",
                                name: "enable_abduct_detection",
                                boxLabel: __("Enable Abduct Detection"),
                                allowBlank: true
                            },
                        ]
                    },
                    {
                        xtype: "fieldset",
                        layout: "column",
                        title: __("Discovery"),
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        collapsible: true,
                        items: [
                            {
                                name: "discovery_policy",
                                xtype: "combobox",
                                fieldLabel: __("Link Discovery Policy"),
                                allowBlank: false,
                                labelWidth: 200,
                                queryMode: "local",
                                displayField: "label",
                                valueField: "id",
                                defaultValue: "R",
                                store: {
                                    fields: ["id", "label"],
                                    data: [
                                        {id: "I", label: "Ignore"},
                                        {id: "O", label: "Create new"},
                                        {id: "R", label: "Replace"},
                                        {id: "C", label: "Cloud"}
                                    ]
                                },
                                uiStyle: "medium"
                            },
                            {
                                name: "status_discovery",
                                xtype: "combobox",
                                fieldLabel: __("Status Discovery"),
                                allowBlank: true,
                                labelWidth: 200,
                                defaultValue: "d",
                                store: [
                                    ["d", __("Disabled")],
                                    ["e", __("Enable")],
                                    ["c", __("Clear Alarm")],
                                    ["ca", __("Clear Alarm if Admin Down")],
                                    ["rc", __("Raise & Clear Alarm")]
                                ],
                                uiStyle: "medium"
                            },
                            {
                                name: "mac_discovery_policy",
                                xtype: "combobox",
                                fieldLabel: __("MAC Discovery Policy"),
                                allowBlank: false,
                                labelWidth: 200,
                                defaultValue: "e",
                                store: [
                                    ["e", __("Transit")],
                                    ["d", __("Disable")],
                                    ["m", __("Management VLAN")],
                                    ["i", __("Direct Downlink")],
                                    ["c", __("Chained Downlink")],
                                    ["u", __("Direct Uplink")],
                                    ["C", __("Cloud Downlink")]
                                ],
                                uiStyle: "medium"
                            },
                            {
                                name: "metric_collected_policy",
                                xtype: "combobox",
                                fieldLabel: __("Metric Collected Policy"),
                                allowBlank: true,
                                labelWidth: 200,
                                defaultValue: "e",
                                store: [
                                    ["e", __("Enabled")],
                                    ["da", __("Disable if Admin Down")],
                                    ["do", __("Disable if Oper Down")]
                                ],
                                uiStyle: "medium"
                            },
                            {
                                name: "allow_lag_mismatch",
                                xtype: "checkbox",
                                boxLabel: __("Allow LAG mismatch"),
                                allowBlank: true
                            },
                            {
                                name: "allow_subinterface_metrics",
                                xtype: "checkbox",
                                boxLabel: __("Apply metrics to subinterfaces"),
                                allowBlank: true
                            },
                        ]
                    },
                    {
                        xtype: "fieldset",
                        layout: "column",
                        title: __("Segment"),
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        collapsible: true,
                        collapsed: true,
                        items: [
                            {
                                name: "allow_autosegmentation",
                                xtype: "checkbox",
                                boxLabel: __("Allow Autosegmentation"),
                                allowBlank: true
                            },
                            {
                                name: "allow_vacuum_bulling",
                                xtype: "checkbox",
                                boxLabel: __("Allow Vacuum Bulling"),
                                allowBlank: true
                            },
                        ]
                    },
                    {
                        xtype: "fieldset",
                        layout: "column",
                        title: __("IfDesc Settings"),
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        collapsible: true,
                        collapsed: true,
                        items: [
                            {
                                name: "ifdesc_patterns",
                                xtype: "inv.ifdescpatterns.LookupField",
                                fieldLabel: __("Patterns"),
                                allowBlank: true
                            },
                            {
                                name: "ifdesc_handler",
                                xtype: "main.handler.LookupField",
                                fieldLabel: __("Handler"),
                                allowBlank: true,
                                query: {
                                    allow_ifdesc: true
                                }
                            }
                        ]
                    },
                    {
                        xtype: "fieldset",
                        layout: "column",
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        defaults: fieldSetDefaults,
                        collapsible: true,
                        collapsed: true,
                        title: __("Integration"),
                        items: [
                            {
                                name: "remote_system",
                                xtype: "main.remotesystem.LookupField",
                                fieldLabel: __("Remote System"),
                                allowBlank: true
                            },
                            {
                                name: "remote_id",
                                xtype: "textfield",
                                fieldLabel: __("Remote ID"),
                                allowBlank: true,
                                uiStyle: "medium"
                            }
                        ]
                    },
                    {
                        name: "metrics",
                        xtype: "gridfield",
                        fieldLabel: __("Metrics"),
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        columns: [
                            {
                                text: __("Metric Type"),
                                dataIndex: "metric_type",
                                width: 250,
                                editor: {
                                    xtype: "pm.metrictype.LookupField"
                                },
                                renderer: NOC.render.Lookup("metric_type")
                            },
                            {
                                text: __("Box"),
                                dataIndex: "enable_box",
                                width: 50,
                                renderer: NOC.render.Bool,
                                editor: "checkbox"
                            },
                            {
                                text: __("Periodic"),
                                dataIndex: "enable_periodic",
                                width: 50,
                                renderer: NOC.render.Bool,
                                editor: "checkbox"
                            },
                            {
                                text: __("Stored"),
                                dataIndex: "is_stored",
                                width: 50,
                                renderer: NOC.render.Bool,
                                editor: "checkbox"
                            },
                            {
                                text: __("Profile"),
                                dataIndex: "threshold_profile",
                                width: 250,
                                editor: {
                                    xtype: "pm.thresholdprofile.LookupField"
                                },
                                renderer: NOC.render.Lookup("threshold_profile")
                            }
                        ]
                    },
                    {
                        name: "match_rules",
                        xtype: "listform",
                        fieldLabel: __("Match Rules"),
                        rows: 5,
                        minWidth: me.formMinWidth,
                        maxWidth: me.formMaxWidth,
                        items: [
                            {
                                name: "dynamic_order",
                                xtype: "numberfield",
                                fieldLabel: __("Dynamic Order"),
                                allowBlank: true,
                                defaultValue: 0,
                                uiStyle: "small"
                            },
                            {
                                name: "labels",
                                xtype: "labelfield",
                                fieldLabel: __("Match Labels"),
                                allowBlank: false,
                                isTree: true,
                                filterProtected: false,
                                pickerPosition: "down",
                                uiStyle: "extra",
                                query: {
                                    "allow_matched": true
                                }
                            },
                            {
                                name: "handler",
                                xtype: "main.handler.LookupField",
                                fieldLabel: __("Match Handler"),
                                allowBlank: true,
                                uiStyle: "medium",
                                query: {
                                    "allow_match_rule": true
                                }
                            }
                        ]
                    }
                ],
                formToolbar: [
                    me.validationSettingsButton
                ]

            }
        );
        me.callParent();
    },
    filters: [
        {
            title: __("By Match Rules Labels"),
            name: "match_rules",
            ftype: "label",
            lookup: "main.handler.LookupField",
            pickerPosition: "left",
            isTree: true,
            filterProtected: false,
            treePickerWidth: 400,
            query_filter: {
                "allow_matched": true
            }
        }
    ],

        //
        onValidationSettings: function() {
            var me = this;
            me.showItem(me.ITEM_VALIDATION_SETTINGS).preview(me.currentRecord);
        }
    ,
        //
        cleanData: function(v) {
            Ext.each(v.metrics, function(m) {
                if(m.low_error === "") {
                    m.low_error = null;
                }
                if(m.low_warn === "") {
                    m.low_warn = null;
                }
                if(m.high_warn === "") {
                    m.high_warn = null;
                }
                if(m.high_error === "") {
                    m.high_error = null;
                }
            });
        }
    });

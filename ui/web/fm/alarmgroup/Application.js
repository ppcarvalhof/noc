//---------------------------------------------------------------------
// fm.alarmgroup application
//---------------------------------------------------------------------
// Copyright (C) 2007-2014 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.fm.alarmgroup.Application");

Ext.define("NOC.fm.alarmgroup.Application", {
    extend: "NOC.core.ModelApplication",
    requires: [
        "NOC.core.label.LabelField",
        "NOC.core.ListFormField",
        "NOC.fm.alarmgroup.Model",
        "NOC.fm.alarmclass.LookupField",
        "NOC.main.notificationgroup.LookupField",
        "Ext.ux.form.MultiIntervalField",
        "NOC.main.handler.LookupField"
    ],
    model: "NOC.fm.alarmgroup.Model",
    columns: [
        {
            text: __("Name"),
            dataIndex: "name",
            width: 100,
            align: "left"
        },
        {
            text: __("Active"),
            dataIndex: "is_active",
            renderer: NOC.render.Bool,
            width: 100,
            align: "left"
        },
        {
            text: __("Group Alarm Class"),
            dataIndex: "group_alarm_class",
            renderer: NOC.render.Lookup("alarm_class"),
            width: 200
        },
        {
            text: __("Reference Prefix"),
            dataIndex: "group_reference",
            width: 150,
            align: "left"
        }
    ],
    fields: [
        {
            name: 'name',
            xtype: 'textfield',
            fieldLabel: __('Name'),
            allowBlank: false,
            uiStyle: 'large'
        },
        {
            name: "is_active",
            xtype: "checkbox",
            boxLabel: __("Active")
        },
        {
            name: 'description',
            xtype: 'textarea',
            fieldLabel: __('Description'),
            uiStyle: 'large'
        },
        {
            xtype: "fieldset",
            layout: "column",
            title: __("Group Alarm"),
            minWidth: me.formMinWidth,
            maxWidth: me.formMaxWidth,
            defaults: fieldSetDefaults,
            collapsible: false,
            items: [
                {
                    name: "group_alarm_class",
                    xtype: "fm.alarmclass.LookupField",
                    fieldLabel: __("Group Alarm Class"),
                    uiStyle: 'large',
                    allowBlank: false
                },
                {
                    name: 'group_reference',
                    xtype: 'textfield',
                    fieldLabel: __('Group Alarm Reference'),
                    uiStyle: 'large'
                },
                {
                    name: 'group_title_template',
                    xtype: 'textarea',
                    fieldLabel: __('Title Template'),
                    uiStyle: 'large'
                }
            ]
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
        },
        {
            name: "notification_group",
            xtype: "main.notificationgroup.LookupField",
            fieldLabel: __("Notification Group"),
            labelWidth: 200,
            allowBlank: true
        },
        {
            name: "rules",
            xtype: "listform",
            fieldLabel: __("Match Rules"),
            rows: 5,
            minWidth: me.formMinWidth,
            maxWidth: me.formMaxWidth,
            items: [
                {
                    name: "labels",
                    xtype: "labelfield",
                    fieldLabel: __("Match Labels"),
                    allowBlank: false,
                    isTree: true,
                    pickerPosition: "down",
                    uiStyle: "extra",
                    query: {
                        "allow_matched": true
                    }
                },
                {
                    name: "alarm_class",
                    xtype: "fm.alarmclass.LookupField",
                    fieldLabel: __("Alarm Class"),
                    uiStyle: 'large',
                    allowBlank: false
                }
            ]
        }
    ]
});

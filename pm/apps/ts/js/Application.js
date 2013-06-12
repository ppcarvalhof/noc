//---------------------------------------------------------------------
// pm.ts application
//---------------------------------------------------------------------
// Copyright (C) 2007-2013 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.pm.ts.Application");

Ext.define("NOC.pm.ts.Application", {
    extend: "NOC.core.ModelApplication",
    uses: [
        "NOC.pm.pmts.Model",
        "NOC.pm.storage.LookupField",
        "NOC.pm.check.LookupField",
        "NOC.pm.ts.TSTypeField"
    ],
    model: "NOC.pm.ts.Model",
    idField: "ts_id",
    columns: [
        {
            text: "Check",
            dataIndex: "check",
            renderer: NOC.render.Lookup("check"),
            width: 200
        },
        {
            text: "Name",
            dataIndex: "name",
            width: 150
        },
        {
            text: "Act.",
            dataIndex: "is_active",
            width: 50,
            renderer: NOC.render.Bool
        },
        {
            text: "Storage",
            dataIndex: "storage",
            renderer: NOC.render.Lookup("storage"),
            width: 150
        },
        {
            text: "Type",
            dataIndex: "type",
            width: 75,
            renderer: NOC.render.Choices({
                G: "Gauge",
                C: "Counter",
                D: "Derive"
            })
        }
    ],
    fields: [
        {
            name: "check",
            fieldLabel: "Check",
            xtype: "pm.check.LookupField"
        },
        {
            name: "name",
            fieldLabel: "Name",
            xtype: "textfield"
        },
        {
            name: "is_active",
            boxLabel: "Active",
            xtype: "checkboxfield"
        },
        {
            name: "storage",
            fieldLabel: "Storage",
            xtype: "pm.storage.LookupField"
        },
        {
            name: "type",
            fieldLabel: "Type",
            xtype: "pm.ts.TSTypeField"
        }
    ],
    //
    onPreview: function(record) {
        var me = this;
        Ext.create("NOC.pm.ts.GraphPreview", {
            title: Ext.String.format("{0} {1}", record.get("check__label"), record.get("name")),
            app: me,
            ts: record.get(me.idField)
        });
    }
});

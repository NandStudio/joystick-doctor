import QtQuick
import QtQuick.Layouts
import "../controls"
import "../glyphs"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 13

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: app.langTick >= 0 ? app.label("diag_title") : ""
                color: theme.ink
                font.family: app.displayFamily
                font.pixelSize: 25
            }
            Item { Layout.fillWidth: true }
            Segment {}
        }

        InkButton {
            text: app.langTick >= 0 ? app.label("calibrate_pad") : ""
            onClicked: app.startGuide()
            Layout.alignment: Qt.AlignLeft
        }

        Text {
            text: app.langTick >= 0 ? app.label("diag_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            visible: app.session !== "ready"
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: {
                    if (app.langTick < 0)
                        return ""
                    if (app.session === "loading")
                        return app.label("reading_hid")
                    if (app.session === "error")
                        return app.sessionDetail
                    return app.label("connect_pad")
                }
                color: theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            InkButton {
                visible: app.session === "error"
                text: app.langTick >= 0 ? app.label("reopen_pad") : ""
                onClicked: app.reopenDevice()
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 18

            LivePad {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 420
            }

            ColumnLayout {
                Layout.preferredWidth: 330
                Layout.maximumWidth: 330
                Layout.fillHeight: true
                spacing: 13

                Text {
                    text: app.langTick >= 0
                          ? app.label(app.viewMode === "virtual" ? "output_virtual" : "entry_physical")
                          : ""
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Rectangle {
                    radius: theme.radiusCard
                    color: theme.surface
                    border.width: theme.edge
                    border.color: theme.stroke
                    Layout.fillWidth: true
                    implicitHeight: stickCol.implicitHeight + 32
                    Column {
                        id: stickCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: app.langTick >= 0 ? app.label("col_stick") : ""
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 12
                        }
                        Text {
                            text: app.stickText
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 15
                            font.weight: 600
                        }
                        Text {
                            text: app.langTick >= 0 ? app.label("col_stick_right") : ""
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 12
                            topPadding: 6
                        }
                        Text {
                            text: app.stickRightText
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 15
                            font.weight: 600
                        }
                    }
                }

                Rectangle {
                    radius: theme.radiusCard
                    color: theme.surface
                    border.width: theme.edge
                    border.color: theme.stroke
                    Layout.fillWidth: true
                    implicitHeight: triggerCol.implicitHeight + 32
                    Column {
                        id: triggerCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: app.langTick >= 0 ? app.label("col_triggers") : ""
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 12
                        }
                        Text {
                            text: "LT  " + app.ltText
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 15
                            font.weight: 600
                        }
                        Rectangle {
                            width: triggerCol.width
                            height: 8
                            radius: 4
                            color: theme.wash
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(1, app.hasSample ? app.lt : 0))
                                height: parent.height
                                radius: 4
                                color: theme.ink
                            }
                        }
                        Text {
                            text: "RT  " + app.rtText
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 15
                            font.weight: 600
                        }
                        Rectangle {
                            width: triggerCol.width
                            height: 8
                            radius: 4
                            color: theme.wash
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(1, app.hasSample ? app.rt : 0))
                                height: parent.height
                                radius: 4
                                color: theme.ink
                            }
                        }
                    }
                }

                Rectangle {
                    visible: app.debugEnabled
                    radius: theme.radiusCard
                    color: theme.surface
                    border.width: theme.edge
                    border.color: theme.stroke
                    Layout.fillWidth: true
                    implicitHeight: linkCol.implicitHeight + 32
                    Column {
                        id: linkCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 8
                        Text {
                            text: app.langTick >= 0 ? app.label("col_link") : ""
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 12
                        }
                        LinkLine {
                            caption: app.langTick >= 0 ? app.label("poll_label") : ""
                            value: app.pollText
                            rowWidth: linkCol.width
                        }
                        LinkLine {
                            caption: app.langTick >= 0 ? app.label("packets_label") : ""
                            value: app.packetText
                            rowWidth: linkCol.width
                        }
                        LinkLine {
                            caption: app.langTick >= 0 ? app.label("deadzone_label") : ""
                            value: app.deadzoneText
                            rowWidth: linkCol.width
                        }
                    }
                }
            }
        }
    }

    component LinkLine: Row {
        property string caption: ""
        property string value: ""
        property real rowWidth: 200
        width: rowWidth
        spacing: 8
        Text {
            text: caption
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 12
            width: 110
        }
        Text {
            text: value
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            font.weight: 600
        }
    }
}

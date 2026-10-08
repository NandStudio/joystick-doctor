import QtQuick
import QtQuick.Layouts
import "../controls"

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 12

        Text {
            text: app.langTick >= 0 ? app.label("log_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("log_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
        }
        Text {
            visible: app.logState === "empty"
            text: app.langTick >= 0 ? app.label("log_empty") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
        }
        Text {
            visible: app.logLast.length > 0
            text: app.logLast
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 17
            font.weight: 600
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentHeight: lines.implicitHeight
            clip: true
            Column {
                id: lines
                width: parent.width
                spacing: 6
                Repeater {
                    model: app.logRows
                    delegate: Row {
                        required property var modelData
                        spacing: 12
                        width: lines.width
                        Text {
                            text: modelData.time
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 13
                            width: 70
                        }
                        Text {
                            text: modelData.level
                            color: modelData.level === "INFO" ? theme.muted : theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 13
                            font.weight: modelData.level === "WARN" ? 600 : 400
                            width: 48
                        }
                        Text {
                            text: modelData.text
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 13
                            width: parent.width - 140
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        RowLayout {
            spacing: 8
            QuietButton {
                visible: app.logState === "ready"
                framed: true
                text: app.langTick >= 0 ? app.label("log_copy") : ""
                onClicked: app.copyLog()
            }
            QuietButton {
                visible: app.logState === "ready"
                framed: true
                text: app.langTick >= 0 ? app.label("log_clear") : ""
                onClicked: app.clearLog()
            }
        }
    }
}

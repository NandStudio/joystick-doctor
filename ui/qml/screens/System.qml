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
        spacing: 16

        Text {
            text: app.langTick >= 0 ? app.label("system_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("system_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
        }

        Rectangle {
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            implicitHeight: vigemCol.implicitHeight + 36
            ColumnLayout {
                id: vigemCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 18
                spacing: 8
                Text {
                    text: "ViGEmBus"
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                }
                Text {
                    text: app.vigemWord
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    font.weight: 600
                }
                Text {
                    visible: app.virtualRunning
                    text: (app.langTick >= 0 ? app.label("slot_label") : "") + "  " + (app.langTick >= 0 ? app.label("slot_name") : "")
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                }
                Text {
                    visible: app.uptimeText.length > 0
                    text: app.uptimeText
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 13
                }
                RowLayout {
                    spacing: 8
                    InkButton {
                        text: app.virtualLabel
                        onClicked: app.toggleVirtual()
                    }
                    QuietButton {
                        visible: app.vigemWord === (app.langTick >= 0 ? app.label("word_absent") : "")
                        framed: true
                        text: app.langTick >= 0 ? app.label("install_driver") : ""
                        onClicked: app.installVigem()
                    }
                }
            }
        }

        Rectangle {
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            implicitHeight: hideCol.implicitHeight + 36
            ColumnLayout {
                id: hideCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 18
                spacing: 8
                Text {
                    text: "HidHide"
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                }
                Text {
                    text: app.hidHideWord
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    font.weight: 600
                }
                Text {
                    text: app.langTick >= 0 ? app.label("hidhide_note") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                RowLayout {
                    spacing: 8
                    QuietButton {
                        framed: true
                        text: app.langTick >= 0 ? app.label("whitelist") : ""
                        onClicked: app.addWhitelist()
                    }
                    QuietButton {
                        framed: true
                        text: app.langTick >= 0 ? app.label("reconnect") : ""
                        onClicked: app.reconnectDevices()
                    }
                    QuietButton {
                        visible: app.hidHideWord === (app.langTick >= 0 ? app.label("word_absent") : "")
                        framed: true
                        text: app.langTick >= 0 ? app.label("install_driver") : ""
                        onClicked: app.installHidHide()
                    }
                }
            }
        }

        Rectangle {
            visible: app.ps3Visible
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            implicitHeight: ps3Col.implicitHeight + 36
            ColumnLayout {
                id: ps3Col
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 18
                spacing: 8
                Text {
                    text: app.ps3Name
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                }
                Text {
                    text: app.ps3Word
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    font.weight: 600
                }
                QuietButton {
                    visible: app.ps3Word === (app.langTick >= 0 ? app.label("word_absent") : "")
                    framed: true
                    text: app.langTick >= 0 ? app.label("install_driver") : ""
                    onClicked: app.installPs3()
                }
            }
        }
        Item { Layout.fillHeight: true }
    }
}

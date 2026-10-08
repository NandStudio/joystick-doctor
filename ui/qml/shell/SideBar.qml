import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../controls"
import "../glyphs"

Rectangle {
    color: theme.surface

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Text {
            text: app.langTick >= 0 ? app.label("mando_label") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 12
            Layout.leftMargin: 8
            Layout.topMargin: 4
        }

        Text {
            visible: app.devices.length === 0
            text: app.langTick >= 0 ? app.label("no_device") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
        }

        Repeater {
            model: app.devices
            delegate: Button {
                id: deviceButton
                required property var modelData
                Layout.fillWidth: true
                implicitHeight: 36
                padding: 0
                onClicked: app.selectDevice(modelData.key)
                background: Item {
                    Rectangle {
                        anchors.fill: parent
                        radius: theme.radiusControl
                        color: deviceButton.hovered || deviceButton.down
                               ? Qt.rgba(0.118, 0.118, 0.118, 0.07) : "transparent"
                    }
                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: -4
                        radius: theme.radiusControl + 4
                        color: "transparent"
                        border.width: 2
                        border.color: deviceButton.activeFocus ? theme.ink : "transparent"
                    }
                }
                contentItem: Item {
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 8
                        Rectangle {
                            width: 8
                            height: 8
                            radius: 4
                            color: theme.ink
                            visible: modelData.open
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: modelData.name
                            color: theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 13
                            font.weight: modelData.open ? 600 : 400
                            elide: Text.ElideRight
                            width: Math.max(0, parent.width - (modelData.open ? 24 : 8))
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }

        Text {
            visible: app.session === "loading"
            text: app.langTick >= 0 ? app.label("opening_pad") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.leftMargin: 8
            Layout.rightMargin: 8
        }

        Item { Layout.preferredHeight: 12 }

        Repeater {
            model: app.destinations
            delegate: QuietButton {
                id: nav
                required property var modelData
                Layout.fillWidth: true
                text: modelData.label
                chosen: app.page === modelData.id
                pill: chosen
                onClicked: app.setPage(modelData.id)
                contentItem: Item {
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        spacing: 8
                    PulseMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "diagnostico"
                    }
                    MiraMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "calibracion"
                    }
                    CurveMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "curvas"
                    }
                    SwapMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "remap"
                    }
                    GearMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "sistema"
                    }
                    RowsMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "ajustes"
                    }
                    CardMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "perfiles"
                    }
                    LogMark {
                        width: 16
                        height: 16
                        mark: nav.chosen ? theme.ink : theme.stroke
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nav.modelData.id === "registro"
                    }
                    Text {
                        text: nav.text
                        color: theme.ink
                        font.family: app.bodyFamily
                        font.pixelSize: 13
                        font.weight: nav.chosen ? 600 : 400
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}

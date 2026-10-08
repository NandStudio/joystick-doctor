import QtQuick
import QtQuick.Layouts
import "../controls"

Rectangle {
    anchors.fill: parent
    visible: app.firstRunOpen
    color: Qt.rgba(43 / 255, 43 / 255, 43 / 255, 0.5)

    Rectangle {
        id: card
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 80)
        height: column.implicitHeight + 52
        radius: theme.radiusCard
        color: theme.surface

        Rectangle {
            z: -1
            anchors.fill: parent
            anchors.topMargin: 12
            radius: theme.radiusCard
            color: Qt.rgba(0.118, 0.118, 0.118, 0.22)
        }

        ColumnLayout {
            id: column
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 26
            spacing: 12
            Text {
                text: app.langTick >= 0 ? app.label("first_title") : ""
                color: theme.ink
                font.family: app.displayFamily
                font.pixelSize: 25
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Text {
                text: app.langTick >= 0 ? app.label("first_body") : ""
                color: theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Text {
                text: app.detectedPad
                color: theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 15
                font.weight: 600
            }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "ViGEmBus"; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; Layout.fillWidth: true }
                Text { text: app.langTick >= 0 ? app.label("required") : ""; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; font.weight: 600 }
            }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "HidHide"; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; Layout.fillWidth: true }
                Text { text: app.langTick >= 0 ? app.label("optional") : ""; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; font.weight: 600 }
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                QuietButton {
                    framed: true
                    text: app.langTick >= 0 ? app.label("later") : ""
                    onClicked: app.dismissFirstRun()
                }
                InkButton {
                    text: app.langTick >= 0 ? app.label("install_both") : ""
                    onClicked: app.installBoth()
                }
            }
        }
    }
}

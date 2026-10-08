import QtQuick
import QtQuick.Controls

Button {
    id: control
    font.family: app.strongFamily
    font.pixelSize: 14
    font.weight: 600
    implicitHeight: 36
    leftPadding: 16
    rightPadding: 16
    spacing: 0

    contentItem: Text {
        text: control.text
        font: control.font
        color: theme.onInk
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Item {
        Rectangle {
            anchors.fill: parent
            radius: theme.radiusControl
            color: control.down ? "#2b2b2b" : theme.ink
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -4
            radius: theme.radiusControl + 4
            color: "transparent"
            border.width: 2
            border.color: control.activeFocus ? theme.ink : "transparent"
        }
    }
}

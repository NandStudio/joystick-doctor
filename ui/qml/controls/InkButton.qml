import QtQuick
import QtQuick.Controls

Button {
    id: control
    property real size: 1
    font.family: app.strongFamily
    font.pixelSize: Math.round(14 * size)
    font.weight: 600
    implicitHeight: Math.round(36 * size)
    leftPadding: Math.round(16 * size)
    rightPadding: Math.round(16 * size)
    topPadding: Math.round(4 * size)
    bottomPadding: Math.round(8 * size)
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
            radius: Math.round(theme.radiusControl * control.size)
            color: control.down ? theme.inkPressed : theme.ink
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -Math.round(4 * control.size)
            radius: Math.round(theme.radiusControl * control.size) + Math.round(4 * control.size)
            color: "transparent"
            border.width: 2
            border.color: control.activeFocus ? theme.ink : "transparent"
        }
    }
}

import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool chosen: false
    property bool pill: false
    property bool framed: false
    font.family: app.bodyFamily
    font.pixelSize: 14
    font.weight: chosen ? 600 : 400
    implicitHeight: 36
    leftPadding: 14
    rightPadding: 14
    spacing: 0

    contentItem: Text {
        text: control.text
        font: control.font
        color: theme.ink
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Item {
        Rectangle {
            anchors.fill: parent
            radius: control.pill ? height / 2 : theme.radiusControl
            color: {
                if (control.chosen)
                    return theme.wash
                if (control.hovered || control.down)
                    return theme.hoverWash
                return "transparent"
            }
            border.width: control.framed ? 1 : 0
            border.color: theme.stroke
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -4
            radius: (control.pill ? parent.height / 2 : theme.radiusControl) + 4
            color: "transparent"
            border.width: 2
            border.color: control.activeFocus ? theme.ink : "transparent"
        }
    }
}

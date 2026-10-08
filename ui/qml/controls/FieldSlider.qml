import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    property string caption: ""
    property real from: 0
    property real to: 100
    property real amount: 0
    signal moved(real amount)
    spacing: 4

    Text {
        text: root.caption
        color: theme.muted
        font.family: app.bodyFamily
        font.pixelSize: 12
    }
    Slider {
        id: slider
        Layout.fillWidth: true
        from: root.from
        to: root.to
        value: root.amount
        onMoved: root.moved(value)
        background: Rectangle {
            x: slider.leftPadding
            y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: slider.availableWidth
            height: 4
            radius: 2
            color: theme.wash
            Rectangle {
                width: slider.visualPosition * parent.width
                height: parent.height
                radius: 2
                color: theme.ink
            }
        }
        handle: Rectangle {
            x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
            y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: 16
            height: 16
            radius: 8
            color: theme.ink
            border.width: slider.activeFocus ? 2 : 0
            border.color: theme.canvas
        }
    }
}

import QtQuick
import QtQuick.Controls

ComboBox {
    id: box
    implicitHeight: 36
    leftPadding: 14
    rightPadding: 28
    font.family: app.bodyFamily
    font.pixelSize: 14

    contentItem: Text {
        leftPadding: box.leftPadding
        rightPadding: box.indicator.width + box.spacing
        text: box.displayText
        font: box.font
        color: theme.ink
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Canvas {
        x: box.width - width - 12
        y: box.topPadding + (box.availableHeight - height) / 2
        width: 10
        height: 6
        property color mark: theme.stroke
        onMarkChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = mark
            ctx.lineWidth = 1.75
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            ctx.beginPath()
            ctx.moveTo(1, 1)
            ctx.lineTo(5, 5)
            ctx.lineTo(9, 1)
            ctx.stroke()
        }
    }

    background: Item {
        Rectangle {
            anchors.fill: parent
            radius: theme.radiusControl
            color: theme.canvas
            border.width: 1
            border.color: theme.stroke
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: -4
            radius: theme.radiusControl + 4
            color: "transparent"
            border.width: 2
            border.color: box.activeFocus ? theme.ink : "transparent"
        }
    }

    popup: Popup {
        y: box.height + 4
        width: box.width
        padding: 4
        contentItem: ListView {
            clip: true
            implicitHeight: Math.min(contentHeight, 6 * 36)
            model: box.popup.visible ? box.delegateModel : null
            currentIndex: box.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                width: 6
                contentItem: Rectangle {
                    implicitWidth: 4
                    radius: 2
                    color: theme.stroke
                }
            }
        }
        background: Rectangle {
            radius: theme.radiusControl
            color: theme.canvas
            border.width: 1
            border.color: theme.stroke
        }
    }

    delegate: ItemDelegate {
        required property var modelData
        required property int index
        width: box.width - 8
        implicitHeight: 36
        height: 36
        padding: 0
        text: modelData
        font.family: app.bodyFamily
        font.pixelSize: 14
        highlighted: box.highlightedIndex === index
        contentItem: Text {
            text: parent.text
            font: parent.font
            color: parent.highlighted ? theme.onWash : theme.ink
            verticalAlignment: Text.AlignVCenter
            leftPadding: 10
        }
        background: Rectangle {
            radius: theme.radiusControl
            color: parent.highlighted ? theme.wash : "transparent"
        }
    }
}

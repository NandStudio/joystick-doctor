import QtQuick

Canvas {
    id: root
    property color mark: theme.stroke
    implicitWidth: 16
    implicitHeight: 16
    onMarkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.strokeStyle = root.mark
        ctx.lineWidth = 1.75
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(3, 3)
        ctx.lineTo(3, 13)
        ctx.moveTo(6, 5)
        ctx.lineTo(13, 5)
        ctx.moveTo(6, 8)
        ctx.lineTo(13, 8)
        ctx.moveTo(6, 11)
        ctx.lineTo(11, 11)
        ctx.stroke()
    }
}

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
        ctx.moveTo(2, 4)
        ctx.lineTo(14, 4)
        ctx.moveTo(2, 8)
        ctx.lineTo(14, 8)
        ctx.moveTo(2, 12)
        ctx.lineTo(10, 12)
        ctx.stroke()
    }
}

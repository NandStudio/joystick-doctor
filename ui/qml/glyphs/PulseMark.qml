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
        ctx.lineJoin = "round"
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(1, height * 0.62)
        ctx.lineTo(width * 0.28, height * 0.62)
        ctx.lineTo(width * 0.42, height * 0.28)
        ctx.lineTo(width * 0.58, height * 0.74)
        ctx.lineTo(width * 0.72, height * 0.62)
        ctx.lineTo(width - 1, height * 0.62)
        ctx.stroke()
    }
}

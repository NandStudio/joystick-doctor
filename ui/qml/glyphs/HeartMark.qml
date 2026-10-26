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
        ctx.moveTo(width * 0.50, height * 0.78)
        ctx.bezierCurveTo(width * 0.16, height * 0.52, width * 0.18, height * 0.26, width * 0.36, height * 0.26)
        ctx.bezierCurveTo(width * 0.46, height * 0.26, width * 0.50, height * 0.34, width * 0.50, height * 0.40)
        ctx.bezierCurveTo(width * 0.50, height * 0.34, width * 0.54, height * 0.26, width * 0.64, height * 0.26)
        ctx.bezierCurveTo(width * 0.82, height * 0.26, width * 0.84, height * 0.52, width * 0.50, height * 0.78)
        ctx.closePath()
        ctx.stroke()
    }
}

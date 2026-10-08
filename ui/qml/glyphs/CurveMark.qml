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
        ctx.lineJoin = "round"
        ctx.beginPath()
        ctx.moveTo(1.5, height - 2)
        ctx.lineTo(width * 0.35, height - 2)
        ctx.lineTo(width * 0.62, height * 0.42)
        ctx.lineTo(width - 1.5, 2)
        ctx.stroke()
    }
}

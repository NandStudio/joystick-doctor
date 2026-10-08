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
        var c = width / 2
        ctx.beginPath()
        ctx.arc(c, height / 2, width * 0.32, 0, Math.PI * 2)
        ctx.moveTo(c, 1.5)
        ctx.lineTo(c, height - 1.5)
        ctx.moveTo(1.5, height / 2)
        ctx.lineTo(width - 1.5, height / 2)
        ctx.stroke()
    }
}

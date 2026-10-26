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
        ctx.fillStyle = root.mark
        ctx.lineWidth = 1.75
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.arc(width / 2, height / 2, 6, 0, Math.PI * 2)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(width / 2, height * 0.42)
        ctx.lineTo(width / 2, height * 0.70)
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(width / 2, height * 0.32, 1.1, 0, Math.PI * 2)
        ctx.fill()
    }
}

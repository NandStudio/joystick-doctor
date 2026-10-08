import QtQuick

Canvas {
    id: root
    property color mark: theme.ink
    implicitWidth: 28
    implicitHeight: 18
    onMarkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.strokeStyle = root.mark
        ctx.lineWidth = 2.75
        ctx.lineJoin = "round"
        ctx.lineCap = "round"
        var x = 1.5
        var y = 1.5
        var w = width - 3
        var h = height - 3
        var r = h * 0.42
        ctx.beginPath()
        ctx.moveTo(x + r, y)
        ctx.lineTo(x + w - r, y)
        ctx.arcTo(x + w, y, x + w, y + r, r)
        ctx.lineTo(x + w, y + h - r)
        ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
        ctx.lineTo(x + r, y + h)
        ctx.arcTo(x, y + h, x, y + h - r, r)
        ctx.lineTo(x, y + r)
        ctx.arcTo(x, y, x + r, y, r)
        ctx.closePath()
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(x + w * 0.32, y + h * 0.58, h * 0.14, 0, Math.PI * 2)
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(x + w * 0.7, y + h * 0.58, h * 0.14, 0, Math.PI * 2)
        ctx.stroke()
    }
}

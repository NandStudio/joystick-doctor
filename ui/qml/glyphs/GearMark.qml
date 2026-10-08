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
        ctx.beginPath()
        ctx.arc(width / 2, height / 2, 3, 0, Math.PI * 2)
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(width / 2, height / 2, 6, 0, Math.PI * 2)
        ctx.stroke()
    }
}

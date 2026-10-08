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
        ctx.strokeRect(2, 3, 12, 10)
        ctx.beginPath()
        ctx.moveTo(2, 6)
        ctx.lineTo(14, 6)
        ctx.stroke()
    }
}

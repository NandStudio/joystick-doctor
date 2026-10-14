import QtQuick
import QtQuick.Effects

Item {
    id: part
    property string file: ""
    property real originX: 0
    property real originY: 0
    property real originW: 1
    property real originH: 1
    property real shiftX: 0
    property real shiftY: 0
    property bool down: false
    property bool active: true
    property color mark: down && active ? theme.ink : theme.stroke

    x: (originX + shiftX) * parent.width / 591.43
    y: (originY + shiftY) * parent.height / 423.76
    width: originW * parent.width / 591.43
    height: originH * parent.height / 423.76
    opacity: active ? 1 : 0.35

    Image {
        id: sourceImage
        anchors.fill: parent
        source: app.assetUrl("xbox-joystick/parts/" + part.file)
        fillMode: Image.PreserveAspectFit
        opacity: 0
        sourceSize.width: Math.max(1, part.width * 2)
        sourceSize.height: Math.max(1, part.height * 2)
    }

    MultiEffect {
        anchors.fill: sourceImage
        source: sourceImage
        colorization: 1
        colorizationColor: part.mark
    }
}

import QtQuick

Item {
    id: root
    property bool dim: !app.hasSample
    property string focusPart: "all"

    function lit(name) {
        return focusPart === "all" || focusPart === name
    }

    function moved(x, y) {
        return x * x + y * y > 0.02
    }

    function nudgeX() {
        var x = 0
        if (app.padLeft)
            x -= 8
        if (app.padRight)
            x += 8
        return root.dim ? 0 : x
    }

    function nudgeY() {
        var y = 0
        if (app.padUp)
            y -= 8
        if (app.padDown)
            y += 8
        return root.dim ? 0 : y
    }

    Item {
        id: board
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height * 591.43 / 423.76)
        height: width * 423.76 / 591.43

        PadPart { file: "body.svg"; originW: 591.43; originH: 423.76; active: true }
        PadPart {
            file: "left-button.svg"
            originX: 76.5; originY: 0; originW: 102.61; originH: 36.71
            down: app.padLb
            active: root.lit("triggers") || root.lit("buttons")
        }
        PadPart {
            file: "right-button.svg"
            originX: 414.5; originY: 0; originW: 100.98; originH: 34.95
            down: app.padRb
            active: root.lit("triggers") || root.lit("buttons")
        }

        PadPart {
            file: "stick-left-well.svg"
            originX: 83.4; originY: 45.9; originW: 90.5; originH: 90.3
            active: root.lit("left")
        }
        PadPart {
            file: "stick-left-ring.svg"
            originX: 92.2; originY: 55.1; originW: 72.8; originH: 72.6
            active: root.lit("left")
        }
        PadPart {
            file: "stick-left-cap.svg"
            originX: 103.9; originY: 67.0; originW: 49.1; originH: 48.9
            shiftX: root.dim ? 0 : app.lx * 14
            shiftY: root.dim ? 0 : -app.ly * 14
            down: !root.dim && (app.padLs || root.moved(app.lx, app.ly))
            active: root.lit("left")
        }

        PadPart {
            file: "dpad-well.svg"
            originX: 150.6; originY: 132.8; originW: 116.4; originH: 116.6
            active: root.lit("buttons")
        }
        PadPart {
            file: "dpad-disc.svg"
            originX: 159.1; originY: 141.2; originW: 99.8; originH: 99.7
            active: root.lit("buttons")
        }
        PadPart {
            file: "dpad-cross.svg"
            originX: 162.7; originY: 143.4; originW: 93.7; originH: 94.8
            shiftX: root.nudgeX()
            shiftY: root.nudgeY()
            down: app.padUp || app.padDown || app.padLeft || app.padRight
            active: root.lit("buttons")
        }

        PadPart {
            file: "stick-right-well.svg"
            originX: 337.7; originY: 148.0; originW: 90.3; originH: 91.0
            active: root.lit("right")
        }
        PadPart {
            file: "stick-right-ring.svg"
            originX: 346.7; originY: 157.0; originW: 72.3; originH: 72.9
            active: root.lit("right")
        }
        PadPart {
            file: "stick-right-cap.svg"
            originX: 358.1; originY: 169.0; originW: 49.3; originH: 48.9
            shiftX: root.dim ? 0 : app.rx * 14
            shiftY: root.dim ? 0 : -app.ry * 14
            down: !root.dim && (app.padRs || root.moved(app.rx, app.ry))
            active: root.lit("right")
        }

        PadPart {
            file: "button-view-ring.svg"
            originX: 220.8; originY: 87.6; originW: 32.2; originH: 25.5
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-view.svg"
            originX: 230.0; originY: 92.7; originW: 11.9; originH: 14.4
            down: app.padBack
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-menu-ring.svg"
            originX: 343.6; originY: 88.1; originW: 31.5; originH: 25.4
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-menu.svg"
            originX: 355.6; originY: 93.0; originW: 11.1; originH: 14.2
            down: app.padStart
            active: root.lit("buttons")
        }

        PadPart {
            file: "button-y.svg"
            originX: 444.7; originY: 35.8; originW: 44.1; originH: 44.2
            down: app.padY
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-x.svg"
            originX: 402.0; originY: 77.0; originW: 43.8; originH: 43.8
            down: app.padX
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-b.svg"
            originX: 486.6; originY: 77.0; originW: 44.2; originH: 43.9
            down: app.padB
            active: root.lit("buttons")
        }
        PadPart {
            file: "button-a.svg"
            originX: 444.8; originY: 117.2; originW: 44.0; originH: 44.6
            down: app.padA
            active: root.lit("buttons")
        }

        FaceLetter {
            glyph: "Y"
            centerX: 466.8; centerY: 57.9
            down: app.padY
            active: root.lit("buttons")
        }
        FaceLetter {
            glyph: "X"
            centerX: 423.9; centerY: 98.9
            down: app.padX
            active: root.lit("buttons")
        }
        FaceLetter {
            glyph: "B"
            centerX: 508.7; centerY: 99.0
            down: app.padB
            active: root.lit("buttons")
        }
        FaceLetter {
            glyph: "A"
            centerX: 466.8; centerY: 139.5
            down: app.padA
            active: root.lit("buttons")
        }

    }

    component FaceLetter: Item {
        property string glyph: ""
        property real centerX: 0
        property real centerY: 0
        property bool down: false
        property bool active: true
        x: (centerX - 14) * board.width / 591.43
        y: (centerY - 14) * board.height / 423.76
        width: 28 * board.width / 591.43
        height: 28 * board.height / 423.76
        opacity: active ? 1 : 0.35
        Text {
            anchors.centerIn: parent
            text: parent.glyph
            color: parent.down && parent.active && !root.dim ? theme.ink : theme.stroke
            font.family: app.bodyFamily
            font.pixelSize: Math.max(10, 16 * board.width / 591.43)
            font.weight: 600
        }
    }

}

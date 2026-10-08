import QtQuick

Item {
    id: root
    property bool dim: !app.hasSample
    property string focusPart: "all"
    property color line: dim ? theme.stroke : theme.ink

    function lit(part) {
        return focusPart === "all" || focusPart === part
    }

    component Cap: Rectangle {
        property string glyph: ""
        property bool down: false
        property bool active: true
        width: 32
        height: 32
        radius: 16
        color: down && active && !root.dim ? theme.ink : "transparent"
        border.width: 2
        border.color: active && !root.dim ? theme.ink : theme.stroke
        Text {
            anchors.centerIn: parent
            text: parent.glyph
            color: parent.down && parent.active && !root.dim ? theme.onInk : parent.border.color
            font.family: app.bodyFamily
            font.pixelSize: 12
            font.weight: 600
        }
    }

    component StickWell: Item {
        property real axisX: 0
        property real axisY: 0
        property bool down: false
        property bool active: true
        property color line: active && !root.dim ? theme.ink : theme.stroke
        width: 88
        height: 88
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: "transparent"
            border.width: 2
            border.color: parent.line
        }
        Rectangle {
            width: 16
            height: 16
            radius: 8
            color: parent.line
            x: parent.width / 2 - width / 2 + (root.dim ? 0 : parent.axisX) * 28
            y: parent.height / 2 - height / 2 - (root.dim ? 0 : parent.axisY) * 28
        }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Item {
            width: parent.width
            height: 32
            Cap {
                glyph: "L"
                width: 48
                down: app.padLb
                active: root.lit("triggers") || root.lit("buttons")
                anchors.left: parent.left
            }
            Cap {
                glyph: "R"
                width: 48
                down: app.padRb
                active: root.lit("triggers") || root.lit("buttons")
                anchors.right: parent.right
            }
        }

        Item {
            width: parent.width
            height: parent.height - 64

            Rectangle {
                anchors.fill: parent
                radius: theme.radiusCard
                color: "transparent"
                border.width: 2.75
                border.color: root.line
            }

            StickWell {
                axisX: app.lx
                axisY: app.ly
                down: app.padLs
                active: root.lit("left")
                anchors.left: parent.left
                anchors.leftMargin: 36
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: -36
            }

            Item {
                width: 72
                height: 72
                anchors.left: parent.left
                anchors.leftMargin: 44
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 28
                opacity: root.lit("buttons") && !root.dim ? 1 : 0.45
                Rectangle { width: 22; height: 22; radius: 4; x: 25; y: 0; color: app.padUp ? theme.ink : "transparent"; border.color: root.line; border.width: 2 }
                Rectangle { width: 22; height: 22; radius: 4; x: 0; y: 25; color: app.padLeft ? theme.ink : "transparent"; border.color: root.line; border.width: 2 }
                Rectangle { width: 22; height: 22; radius: 4; x: 50; y: 25; color: app.padRight ? theme.ink : "transparent"; border.color: root.line; border.width: 2 }
                Rectangle { width: 22; height: 22; radius: 4; x: 25; y: 50; color: app.padDown ? theme.ink : "transparent"; border.color: root.line; border.width: 2 }
            }

            Item {
                width: 112
                height: 120
                anchors.right: parent.right
                anchors.rightMargin: 48
                anchors.top: parent.top
                anchors.topMargin: 28
                opacity: root.lit("buttons") && !root.dim ? 1 : 0.45
                Cap { glyph: "Y"; anchors.horizontalCenter: parent.horizontalCenter; y: 0; down: app.padY; active: true }
                Cap { glyph: "X"; x: 0; y: 44; down: app.padX; active: true }
                Cap { glyph: "B"; x: 80; y: 44; down: app.padB; active: true }
                Cap { glyph: "A"; anchors.horizontalCenter: parent.horizontalCenter; y: 88; down: app.padA; active: true }
            }

            StickWell {
                axisX: app.rx
                axisY: app.ry
                down: app.padRs
                active: root.lit("right")
                anchors.right: parent.right
                anchors.rightMargin: 64
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 24
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                opacity: root.lit("buttons") && !root.dim ? 1 : 0.45
                Cap { glyph: "−"; width: 36; down: app.padBack; active: true }
                Cap { glyph: "G"; down: app.padGuide; active: true }
                Cap { glyph: "+"; width: 36; down: app.padStart; active: true }
            }
        }
    }
}

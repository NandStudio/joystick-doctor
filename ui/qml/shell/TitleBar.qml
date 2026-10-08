import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "../controls"
import "../glyphs"

Rectangle {
    id: root
    color: theme.surface
    implicitHeight: 44

    MouseArea {
        anchors.fill: parent
        onPressed: Window.window.startSystemMove()
        onDoubleClicked: {
            if (Window.window.visibility === Window.Maximized)
                Window.window.showNormal()
            else
                Window.window.showMaximized()
        }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8
        PadMark {
            width: 28
            height: 18
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            text: app.guideOpen ? (app.langTick >= 0 ? app.label("guide_title") : "") : "Joystick Doctor"
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 15
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            visible: app.guideOpen
            text: app.guideStep
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 13
            font.weight: 600
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Row {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0

        Item {
            width: app.guideOpen ? exitGuide.implicitWidth + 8 : 0
            height: 44
            visible: app.guideOpen
            QuietButton {
                id: exitGuide
                anchors.verticalCenter: parent.verticalCenter
                text: app.langTick >= 0 ? app.label("guide_exit") : ""
                onClicked: app.exitGuide()
            }
        }

        component WinButton: Button {
            id: win
            property bool closes: false
            implicitWidth: 46
            implicitHeight: 44
            padding: 0
            background: Rectangle {
                color: {
                    if (!win.hovered && !win.down)
                        return "transparent"
                    if (win.closes)
                        return theme.ink
                    return theme.hoverWash
                }
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: 4
                color: "transparent"
                border.width: 2
                border.color: win.activeFocus ? theme.ink : "transparent"
                radius: theme.radiusSmall
            }
        }

        WinButton {
            Accessible.name: app.langTick >= 0 ? app.label("win_min") : ""
            onClicked: Window.window.showMinimized()
            Rectangle {
                width: 12
                height: 2
                anchors.centerIn: parent
                color: theme.ink
            }
        }
        WinButton {
            Accessible.name: app.langTick >= 0
                    ? app.label(Window.window.visibility === Window.Maximized ? "win_restore" : "win_max")
                    : ""
            onClicked: {
                if (Window.window.visibility === Window.Maximized)
                    Window.window.showNormal()
                else
                    Window.window.showMaximized()
            }
            Rectangle {
                width: 12
                height: 12
                anchors.centerIn: parent
                color: "transparent"
                border.width: 2
                border.color: theme.ink
                radius: 2
            }
        }
        WinButton {
            closes: true
            Accessible.name: app.langTick >= 0 ? app.label("win_close") : ""
            onClicked: Window.window.close()
            Text {
                anchors.centerIn: parent
                text: "×"
                color: parent.closes && parent.hovered ? theme.onInk : theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 18
            }
        }
    }
}

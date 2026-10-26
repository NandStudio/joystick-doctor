import QtQuick
import QtQuick.Window
import QtQuick.Controls
import "shell"
import "screens"

Window {
    id: win
    width: 1280
    height: 800
    minimumWidth: 1280
    minimumHeight: 800
    visible: true
    title: "Joystick Doctor"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint

    FontLoader {
        id: displayFont
        source: app.fontUrl("Caprasimo-Regular.ttf")
    }
    FontLoader {
        id: bodyFont
        source: app.fontUrl("Figtree-Regular.ttf")
    }
    FontLoader {
        id: strongFont
        source: app.fontUrl("Figtree-SemiBold.ttf")
    }

    function publishFonts() {
        if (displayFont.status !== FontLoader.Ready)
            return
        if (bodyFont.status !== FontLoader.Ready)
            return
        if (strongFont.status !== FontLoader.Ready)
            return
        app.setFontFamilies(displayFont.name, bodyFont.name, strongFont.name)
    }

    Component.onCompleted: publishFonts()
    Connections {
        target: displayFont
        function onStatusChanged() { win.publishFonts() }
    }
    Connections {
        target: bodyFont
        function onStatusChanged() { win.publishFonts() }
    }
    Connections {
        target: strongFont
        function onStatusChanged() { win.publishFonts() }
    }

    Rectangle {
        id: shell
        anchors.fill: parent
        radius: win.visibility === Window.Maximized ? 0 : theme.radiusControl
        color: theme.canvas
        clip: true

    TitleBar {
        id: titleBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 44
    }

    SideBar {
        id: sideBar
        anchors.left: parent.left
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        width: 218
    }

    Diagnosis {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "diagnostico"
    }

    Calibration {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "calibracion"
    }

    Curves {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "curvas"
    }

    Remap {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "remap"
    }

    System {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "sistema"
    }

    Settings {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "ajustes"
    }

    Profiles {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "perfiles"
    }

    Log {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "registro"
    }

    Vibration {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "vibracion"
    }

    About {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "acerca"
    }

    StatusBar {
        id: statusBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 44
    }

    GuideOverlay {
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 5
    }

    FirstRun {
        z: 8
    }

    ConfirmDialog {
        z: 10
    }
    }

    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (app.confirmOpen)
                app.confirmNo()
            else if (app.firstRunOpen)
                app.dismissFirstRun()
            else if (app.remapEditorOpen)
                app.cancelRule()
            else if (app.guideOpen)
                app.exitGuide()
        }
    }

    onClosing: function(close) {
        app.shutdown()
        close.accepted = true
    }
}

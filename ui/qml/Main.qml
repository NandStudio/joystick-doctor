import QtQuick
import QtQuick.Window
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
    color: theme.canvas
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

    Diagnostico {
        anchors.left: sideBar.right
        anchors.right: parent.right
        anchors.top: titleBar.bottom
        anchors.bottom: statusBar.top
        visible: app.page === "diagnostico"
    }

    StatusBar {
        id: statusBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 44
    }

    ConfirmDialog {
        z: 10
    }

    onClosing: function(close) {
        app.shutdown()
        close.accepted = true
    }
}

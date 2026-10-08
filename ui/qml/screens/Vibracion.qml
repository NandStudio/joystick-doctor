import QtQuick
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 16

        Text {
            text: app.langTick >= 0 ? app.label("rumble_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("rumble_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.maximumWidth: 640
        }
        Text {
            text: app.session === "empty"
                  ? (app.langTick >= 0 ? app.label("rumble_no_pad") : "")
                  : (app.langTick >= 0 ? app.label("rumble_none") : "")
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 32
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.maximumWidth: 640
            Layout.topMargin: 12
        }
        Item { Layout.fillHeight: true }
    }
}

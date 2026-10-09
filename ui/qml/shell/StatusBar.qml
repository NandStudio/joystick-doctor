import QtQuick
import QtQuick.Layouts

Rectangle {
    color: theme.surface
    border.width: theme.edge
    border.color: theme.stroke
    implicitHeight: 44

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 12
        spacing: 18

        component StatusWord: Row {
            property string caption: ""
            property string value: ""
            spacing: 6
            Text {
                text: caption
                color: theme.muted
                font.family: app.bodyFamily
                font.pixelSize: 12
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: value
                color: theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 13
                font.weight: 600
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        StatusWord {
            caption: app.langTick >= 0 ? app.label("status_vigem") : ""
            value: app.vigemWord
        }
        StatusWord {
            caption: app.langTick >= 0 ? app.label("status_hidhide") : ""
            value: app.hidHideWord
        }
        StatusWord {
            visible: app.debugEnabled
            caption: app.langTick >= 0 ? app.label("status_poll") : ""
            value: app.pollText
        }
        StatusWord {
            caption: app.langTick >= 0 ? app.label("status_profile") : ""
            value: app.profileWord
        }

        Item { Layout.fillWidth: true }

        Text {
            visible: app.notice.length > 0
            text: app.notice
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 12
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }
}

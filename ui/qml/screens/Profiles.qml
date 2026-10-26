import QtQuick
import QtQuick.Layouts
import "../controls"

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 16

        Text {
            text: app.langTick >= 0 ? app.label("profiles_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("profiles_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            visible: app.profileState === "loading"
            text: app.langTick >= 0 ? app.label("profiles_loading") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
        }
        Text {
            visible: app.profileState === "empty"
            text: app.langTick >= 0 ? app.label("profiles_empty") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
        }
        InkButton {
            visible: app.profileState === "empty"
            text: app.langTick >= 0 ? app.label("new_profile") : ""
            onClicked: app.createProfile()
        }

        Text {
            visible: app.profileState === "error"
            text: app.langTick >= 0 ? app.label("profiles_error") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        QuietButton {
            visible: app.profileState === "error"
            framed: true
            text: app.langTick >= 0 ? app.label("open_from_settings") : ""
            onClicked: app.setPage("ajustes")
        }

        Rectangle {
            visible: app.profileState === "ready"
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            Layout.maximumWidth: 520
            implicitHeight: card.implicitHeight + 36
            ColumnLayout {
                id: card
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 18
                spacing: 8
                Text {
                    text: app.langTick >= 0 ? app.label("profile_saved_word") : ""
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                }
                Text {
                    text: app.profileCardName
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    font.weight: 600
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Text {
                    text: app.profileCardDetail
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                QuietButton {
                    framed: true
                    text: app.langTick >= 0 ? app.label("edit_profile") : ""
                    onClicked: app.editProfile()
                }
            }
        }
        Item { Layout.fillHeight: true }
    }
}

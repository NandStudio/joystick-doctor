import QtQuick
import QtQuick.Controls
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
            text: app.langTick >= 0 ? app.label("settings_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("settings_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
        }
        Text {
            visible: app.settingsState === "error"
            text: app.langTick >= 0 ? app.label("settings_error") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
            spacing: 16

            Rectangle {
                radius: theme.radiusCard
                color: theme.surface
                Layout.preferredWidth: 420
                Layout.maximumWidth: 420
                implicitHeight: generalCol.implicitHeight + 36
                ColumnLayout {
                    id: generalCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 18
                    spacing: 8
                    Text {
                        text: app.langTick >= 0 ? app.label("settings_general") : ""
                        color: theme.ink
                        font.family: app.displayFamily
                        font.pixelSize: 17
                    }
                    Text {
                        text: app.langTick >= 0 ? app.label("language") : ""
                        color: theme.muted
                        font.family: app.bodyFamily
                        font.pixelSize: 12
                    }
                    ComboBox {
                        Layout.fillWidth: true
                        font.family: app.bodyFamily
                        font.pixelSize: 14
                        model: [
                            app.langTick >= 0 ? app.label("lang_system") : "",
                            app.langTick >= 0 ? app.label("lang_en") : "",
                            app.langTick >= 0 ? app.label("lang_es") : ""
                        ]
                        currentIndex: app.languagePref === "en" ? 1 : (app.languagePref === "es" ? 2 : 0)
                        onActivated: {
                            var prefs = ["system", "en", "es"]
                            app.setLanguagePref(prefs[currentIndex])
                        }
                    }
                }
            }

            Rectangle {
                radius: theme.radiusCard
                color: theme.surface
                Layout.preferredWidth: 420
                Layout.maximumWidth: 420
                implicitHeight: folderCol.implicitHeight + 36
                ColumnLayout {
                    id: folderCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 18
                    spacing: 12
                    Text {
                        text: app.langTick >= 0 ? app.label("settings_folder") : ""
                        color: theme.ink
                        font.family: app.displayFamily
                        font.pixelSize: 17
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    QuietButton {
                        framed: true
                        text: app.langTick >= 0 ? app.label("open_folder") : ""
                        onClicked: app.openConfigFolder()
                    }
                }
            }
        }
        Item { Layout.fillHeight: true }
    }
}

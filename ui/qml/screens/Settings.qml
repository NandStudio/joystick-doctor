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
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            spacing: 16

            ColumnLayout {
                Layout.preferredWidth: 420
                Layout.maximumWidth: 420
                Layout.alignment: Qt.AlignTop
                spacing: 16

                Rectangle {
                    radius: theme.radiusCard
                    color: theme.surface
                    border.width: theme.edge
                    border.color: theme.stroke
                    Layout.fillWidth: true
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
                        FieldCombo {
                            id: languageBox
                            Layout.fillWidth: true
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
                        Text {
                            text: app.langTick >= 0 ? app.label("theme_label") : ""
                            color: theme.muted
                            font.family: app.bodyFamily
                            font.pixelSize: 12
                            Layout.topMargin: 8
                        }
                        QuietButton {
                            framed: true
                            text: app.langTick >= 0 ? app.label("theme_light") : ""
                            chosen: !theme.isDark && !theme.isContrast
                            onClicked: app.setTheme("light")
                            Layout.fillWidth: true
                        }
                        QuietButton {
                            framed: true
                            text: app.langTick >= 0 ? app.label("theme_dark") : ""
                            chosen: theme.isDark
                            onClicked: app.setTheme("dark")
                            Layout.fillWidth: true
                        }
                        QuietButton {
                            framed: true
                            text: app.langTick >= 0 ? app.label("theme_contrast") : ""
                            chosen: theme.isContrast
                            onClicked: app.setTheme("contrast")
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle {
                    radius: theme.radiusCard
                    color: theme.surface
                    border.width: theme.edge
                    border.color: theme.stroke
                    Layout.fillWidth: true
                    implicitHeight: debugCol.implicitHeight + 36
                    ColumnLayout {
                        id: debugCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 18
                        spacing: 12
                        Text {
                            text: app.langTick >= 0 ? app.label("debug_title") : ""
                            color: theme.ink
                            font.family: app.displayFamily
                            font.pixelSize: 17
                        }
                        QuietButton {
                            framed: true
                            text: app.langTick >= 0 ? app.label(app.debugEnabled ? "debug_on" : "debug_off") : ""
                            chosen: app.debugEnabled
                            onClicked: app.setDebug(!app.debugEnabled)
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Rectangle {
                radius: theme.radiusCard
                color: theme.surface
                border.width: theme.edge
                border.color: theme.stroke
                Layout.preferredWidth: 420
                Layout.maximumWidth: 420
                Layout.alignment: Qt.AlignTop
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

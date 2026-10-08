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
                        id: languageBox
                        Layout.fillWidth: true
                        implicitHeight: 36
                        leftPadding: 14
                        rightPadding: 28
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

                        contentItem: Text {
                            leftPadding: languageBox.leftPadding
                            rightPadding: languageBox.indicator.width + languageBox.spacing
                            text: languageBox.displayText
                            font: languageBox.font
                            color: theme.ink
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }

                        indicator: Canvas {
                            x: languageBox.width - width - 12
                            y: languageBox.topPadding + (languageBox.availableHeight - height) / 2
                            width: 10
                            height: 6
                            property color mark: theme.stroke
                            onMarkChanged: requestPaint()
                            onPaint: {
                                var ctx = getContext("2d")
                                ctx.reset()
                                ctx.strokeStyle = mark
                                ctx.lineWidth = 1.75
                                ctx.lineCap = "round"
                                ctx.lineJoin = "round"
                                ctx.beginPath()
                                ctx.moveTo(1, 1)
                                ctx.lineTo(5, 5)
                                ctx.lineTo(9, 1)
                                ctx.stroke()
                            }
                        }

                        background: Item {
                            Rectangle {
                                anchors.fill: parent
                                radius: theme.radiusControl
                                color: theme.canvas
                                border.width: 1
                                border.color: theme.stroke
                            }
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: -4
                                radius: theme.radiusControl + 4
                                color: "transparent"
                                border.width: 2
                                border.color: languageBox.activeFocus ? theme.ink : "transparent"
                            }
                        }

                        popup: Popup {
                            y: languageBox.height + 4
                            width: languageBox.width
                            padding: 4
                            contentItem: ListView {
                                clip: true
                                implicitHeight: contentHeight
                                model: languageBox.popup.visible ? languageBox.delegateModel : null
                                currentIndex: languageBox.highlightedIndex
                            }
                            background: Rectangle {
                                radius: theme.radiusControl
                                color: theme.canvas
                                border.width: 1
                                border.color: theme.stroke
                            }
                        }

                        delegate: ItemDelegate {
                            required property var modelData
                            required property int index
                            width: languageBox.width - 8
                            text: modelData
                            font.family: app.bodyFamily
                            font.pixelSize: 14
                            highlighted: languageBox.highlightedIndex === index
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: theme.ink
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 10
                            }
                            background: Rectangle {
                                radius: theme.radiusControl
                                color: parent.highlighted ? theme.wash : "transparent"
                            }
                        }
                    }
                    Text {
                        text: app.langTick >= 0 ? app.label("theme_label") : ""
                        color: theme.muted
                        font.family: app.bodyFamily
                        font.pixelSize: 12
                        Layout.topMargin: 8
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        QuietButton {
                            text: app.langTick >= 0 ? app.label("theme_light") : ""
                            chosen: !theme.isDark
                            onClicked: app.setTheme("light")
                            Layout.fillWidth: true
                        }
                        QuietButton {
                            text: app.langTick >= 0 ? app.label("theme_dark") : ""
                            chosen: theme.isDark
                            onClicked: app.setTheme("dark")
                            Layout.fillWidth: true
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

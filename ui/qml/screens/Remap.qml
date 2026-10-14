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
        spacing: 12

        Text {
            text: app.langTick >= 0 ? app.label("remap_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("remap_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Text {
            visible: app.remapDetail.length > 0
            text: app.remapDetail
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            Layout.fillWidth: true
        }

        Row {
            spacing: 12
            Text { text: app.langTick >= 0 ? app.label("col_physical") : ""; width: 180; color: theme.muted; font.family: app.bodyFamily; font.pixelSize: 12 }
            Text { text: app.langTick >= 0 ? app.label("col_virtual") : ""; width: 160; color: theme.muted; font.family: app.bodyFamily; font.pixelSize: 12 }
            Text { text: app.langTick >= 0 ? app.label("col_mode") : ""; width: 160; color: theme.muted; font.family: app.bodyFamily; font.pixelSize: 12 }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentHeight: ruleCol.implicitHeight + 8
            clip: true
            Column {
                id: ruleCol
                y: 4
                width: parent.width
                spacing: 8
                Repeater {
                    model: app.remapRows
                    delegate: RowLayout {
                        required property var modelData
                        width: ruleCol.width
                        spacing: 12
                        Text { text: modelData.physical; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; Layout.preferredWidth: 180; elide: Text.ElideRight }
                        Text { text: modelData.virtual; color: theme.ink; font.family: app.bodyFamily; font.pixelSize: 15; Layout.preferredWidth: 160 }
                        Text {
                            text: modelData.mode
                            color: modelData.mode === (app.langTick >= 0 ? app.label("word_error") : "") ? theme.ink : theme.ink
                            font.family: app.bodyFamily
                            font.pixelSize: 15
                            font.weight: modelData.mode === (app.langTick >= 0 ? app.label("word_error") : "") ? 600 : 400
                            Layout.preferredWidth: 160
                        }
                        QuietButton {
                            text: app.langTick >= 0 ? app.label("change_rule") : ""
                            onClicked: app.beginEditRule(modelData.index)
                        }
                    }
                }
            }
        }

        RowLayout {
            spacing: 8
            InkButton {
                text: app.langTick >= 0 ? app.label("add_rule") : ""
                onClicked: app.beginAddRule()
            }
            QuietButton {
                visible: app.remapRows.length > 0
                framed: true
                text: app.langTick >= 0 ? app.label("reset_rules") : ""
                onClicked: app.resetRules()
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: app.remapEditorOpen
        color: theme.veil
        Rectangle {
            anchors.centerIn: parent
            width: Math.min(640, parent.width - 80)
            height: Math.min(560, parent.height - 40)
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 8
                Text {
                    text: app.langTick >= 0 ? app.label("remap_sources_label") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 12
                }
                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentHeight: sourceFlow.implicitHeight + 8
                    clip: true
                    Flow {
                        id: sourceFlow
                        y: 4
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: app.remapSources
                            delegate: QuietButton {
                                required property var modelData
                                text: modelData.label
                                chosen: modelData.on
                                onClicked: app.toggleRemapSource(modelData.key)
                            }
                        }
                    }
                }
                Text {
                    text: app.langTick >= 0 ? app.label("remap_dest_label") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 12
                }
                FieldCombo {
                    model: app.buttonNames
                    currentIndex: app.remapDestIndex
                    onActivated: app.setRemapDest(currentIndex)
                    Layout.fillWidth: true
                }
                Text {
                    text: app.langTick >= 0 ? app.label("remap_hold_label") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 12
                }
                FieldCombo {
                    model: app.holdNames
                    currentIndex: app.remapHoldIndex
                    onActivated: app.setRemapHold(currentIndex)
                    Layout.fillWidth: true
                }
                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 8
                    QuietButton {
                        framed: true
                        text: app.langTick >= 0 ? app.label("cancel") : ""
                        onClicked: app.cancelRule()
                    }
                    InkButton {
                        text: app.langTick >= 0 ? app.label("save_rule") : ""
                        onClicked: app.commitRule()
                    }
                }
            }
        }
    }
}

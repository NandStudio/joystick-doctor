import QtQuick
import QtQuick.Layouts
import "../controls"
import "../glyphs"

Rectangle {
    color: theme.canvas
    visible: app.guideOpen

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 12

        Text {
            text: app.guideHeading
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 32
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Text {
            text: app.guideBody
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.maximumWidth: 720
            Layout.alignment: Qt.AlignHCenter
        }

        LivePad {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.maximumHeight: 360
            focusPart: app.guideFocus
            dim: app.guidePhase === "empty"
        }

        Text {
            visible: app.guidePhase === "measuring"
            text: app.langTick >= 0 ? app.label("guide_measuring") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 15
            Layout.alignment: Qt.AlignHCenter
        }
        Text {
            visible: app.guideMeasure.length > 0
            text: app.guideMeasure
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            font.weight: 600
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }
        Text {
            visible: app.guideError.length > 0
            text: app.guideError
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 8
            QuietButton {
                visible: app.guideShowBack
                framed: true
                text: app.langTick >= 0 ? app.label("guide_back") : ""
                onClicked: app.guideBack()
            }
            InkButton {
                text: app.guideNextLabel
                onClicked: app.guideNext()
            }
        }

        Row {
            Layout.alignment: Qt.AlignHCenter
            spacing: 8
            Repeater {
                model: 5
                delegate: Rectangle {
                    required property int index
                    width: 8
                    height: 8
                    radius: 4
                    color: theme.ink
                    opacity: index === app.guideIndex ? 1 : 0.28
                }
            }
        }
        Text {
            text: app.langTick >= 0 ? app.label("guide_repeat") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 12
            Layout.alignment: Qt.AlignHCenter
        }
    }
}

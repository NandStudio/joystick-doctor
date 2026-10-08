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
        spacing: 13

        Text {
            text: app.langTick >= 0 ? app.label("cal_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("cal_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Text {
            visible: app.calWord.length > 0
            text: app.calWord
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 32
            Layout.topMargin: 18
        }
        Text {
            text: app.calDetail
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.maximumWidth: 640
        }

        RowLayout {
            Layout.topMargin: 8
            spacing: 8
            InkButton {
                text: app.langTick >= 0 ? app.label("recalibrate") : ""
                onClicked: app.startGuide()
            }
            QuietButton {
                framed: true
                text: app.langTick >= 0 ? app.label("factory") : ""
                onClicked: app.restoreFactory()
            }
            QuietButton {
                framed: true
                text: app.langTick >= 0 ? app.label("export_report") : ""
                onClicked: app.exportReport()
            }
        }
        Item { Layout.fillHeight: true }
    }
}

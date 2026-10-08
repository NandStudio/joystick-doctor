import QtQuick
import QtQuick.Layouts
import "../controls"

Rectangle {
    id: root
    anchors.fill: parent
    color: theme.veil
    visible: app.confirmOpen
    focus: visible

    Keys.onEscapePressed: function(event) {
        app.confirmNo()
        event.accepted = true
    }

    onVisibleChanged: {
        if (visible)
            noButton.forceActiveFocus()
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 80)
        height: dialogColumn.implicitHeight + 52
        radius: theme.radiusCard
        color: theme.surface

        ColumnLayout {
            id: dialogColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 26
            spacing: 16

            Text {
                text: app.confirmTitle
                color: theme.ink
                font.family: app.displayFamily
                font.pixelSize: 25
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Text {
                text: app.confirmBody
                color: theme.ink
                font.family: app.bodyFamily
                font.pixelSize: 15
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                QuietButton {
                    id: noButton
                    framed: true
                    text: app.langTick >= 0 ? app.label("no") : ""
                    onClicked: app.confirmNo()
                }
                InkButton {
                    text: app.langTick >= 0 ? app.label("yes") : ""
                    onClicked: app.confirmYes()
                }
            }
        }
    }
}

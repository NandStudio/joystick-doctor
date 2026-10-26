import QtQuick
import QtQuick.Layouts
import "../controls"

Rectangle {
    id: card
    visible: app.thanksOpen
    radius: theme.radiusCard
    color: theme.surface
    border.width: theme.edge > 0 ? theme.edge : 1
    border.color: theme.stroke
    implicitHeight: column.implicitHeight + 36
    implicitWidth: column.implicitWidth + 36

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 18
        spacing: 12

        Text {
            text: app.langTick >= 0 ? app.label("thanks_body") : ""
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        InkButton {
            text: app.langTick >= 0 ? app.label("donate") : ""
            onClicked: app.thanksSupport()
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            QuietButton {
                id: laterButton
                framed: true
                text: app.langTick >= 0 ? app.label("thanks_later") : ""
                onClicked: app.thanksLater()
            }
            QuietButton {
                framed: true
                text: app.langTick >= 0 ? app.label("thanks_never") : ""
                onClicked: app.thanksNever()
            }
        }
    }

    Keys.onEscapePressed: function(event) {
        app.thanksLater()
        event.accepted = true
    }

    onVisibleChanged: {
        if (visible)
            laterButton.forceActiveFocus()
    }
}

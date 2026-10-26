import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../controls"
import "../glyphs"

Item {
    component MetaLink: Button {
        id: meta
        property string linkKey: ""
        padding: 0
        leftPadding: 2
        rightPadding: 2
        implicitWidth: metaLabel.implicitWidth + leftPadding + rightPadding
        implicitHeight: 28
        font.family: app.bodyFamily
        font.pixelSize: 13
        onClicked: app.openLink(linkKey)
        background: Rectangle {
            anchors.fill: parent
            radius: 4
            color: "transparent"
            border.width: 2
            border.color: meta.activeFocus ? theme.ink : "transparent"
        }
        contentItem: Text {
            id: metaLabel
            text: meta.text
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 13
            font.underline: meta.hovered
            verticalAlignment: Text.AlignVCenter
        }
    }

    component CreditRow: Button {
        id: credit
        property string title: ""
        property string status: ""
        property string detail: ""
        property string linkKey: ""
        Layout.fillWidth: true
        leftPadding: 12
        rightPadding: 12
        topPadding: 10
        bottomPadding: 10
        implicitHeight: Math.max(44, creditBody.implicitHeight + topPadding + bottomPadding)
        onClicked: app.openLink(linkKey)
        background: Item {
            Rectangle {
                anchors.fill: parent
                radius: theme.radiusControl
                color: credit.hovered || credit.down ? theme.hoverWash : "transparent"
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: 2
                radius: Math.max(0, theme.radiusControl - 2)
                color: "transparent"
                border.width: 2
                border.color: credit.activeFocus ? theme.ink : "transparent"
            }
        }
        contentItem: RowLayout {
            spacing: 12
            ColumnLayout {
                id: creditBody
                Layout.fillWidth: true
                spacing: 2
                RowLayout {
                    spacing: 8
                    Layout.fillWidth: true
                    Text {
                        text: credit.title
                        color: theme.ink
                        font.family: app.bodyFamily
                        font.pixelSize: 15
                        font.weight: 600
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    Text {
                        text: credit.status
                        color: theme.ink
                        font.family: app.bodyFamily
                        font.pixelSize: 13
                        font.weight: 600
                    }
                }
                Text {
                    text: credit.detail
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 26
        anchors.bottomMargin: 30
        spacing: 16

        Text {
            text: app.langTick >= 0 ? app.label("about_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }

        Flow {
            Layout.fillWidth: true
            spacing: 0
            Text {
                text: "Joystick Doctor  ·  v" + app.appVersion + "  ·  "
                color: theme.muted
                font.family: app.bodyFamily
                font.pixelSize: 13
            }
            MetaLink {
                text: app.langTick >= 0 ? app.label("about_license") : ""
                linkKey: "gpl"
            }
            Text {
                text: "  ·  "
                color: theme.muted
                font.family: app.bodyFamily
                font.pixelSize: 13
            }
            MetaLink {
                text: app.langTick >= 0 ? app.label("about_code") : ""
                linkKey: "github"
            }
        }

        Rectangle {
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            Layout.maximumWidth: 560
            implicitHeight: supportCol.implicitHeight + 36
            ColumnLayout {
                id: supportCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 18
                spacing: 12
                Text {
                    text: app.langTick >= 0 ? app.label("about_support_title") : ""
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Text {
                    text: app.langTick >= 0 ? app.label("about_body") : ""
                    color: theme.ink
                    font.family: app.bodyFamily
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                InkButton {
                    id: coffee
                    implicitWidth: coffeeRow.implicitWidth + leftPadding + rightPadding
                    onClicked: app.openLink("cafecito")
                    contentItem: Row {
                        id: coffeeRow
                        spacing: 8
                        HeartMark {
                            width: 16
                            height: 16
                            mark: theme.onInk
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: app.langTick >= 0 ? app.label("about_coffee") : ""
                            color: theme.onInk
                            font.family: app.strongFamily
                            font.pixelSize: 14
                            font.weight: 600
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }

        Rectangle {
            radius: theme.radiusCard
            color: theme.surface
            border.width: theme.edge
            border.color: theme.stroke
            Layout.fillWidth: true
            Layout.maximumWidth: 560
            implicitHeight: creditCol.implicitHeight + 28
            ColumnLayout {
                id: creditCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                anchors.topMargin: 18
                spacing: 4
                Text {
                    text: app.langTick >= 0 ? app.label("about_credits_title") : ""
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    Layout.leftMargin: 12
                    Layout.rightMargin: 12
                    Layout.bottomMargin: 4
                }
                CreditRow {
                    title: "ViGEmBus, " + (app.langTick >= 0 ? app.label("about_by") : "")
                    status: app.langTick >= 0 ? app.label("about_visit") : ""
                    detail: app.langTick >= 0 ? app.label("about_vigem_note") : ""
                    linkKey: "vigem"
                }
                CreditRow {
                    title: "HidHide, " + (app.langTick >= 0 ? app.label("about_by") : "")
                    status: app.langTick >= 0 ? app.label("about_visit") : ""
                    detail: app.langTick >= 0 ? app.label("about_hid_note") : ""
                    linkKey: "hidhide"
                }
            }
        }
        Item { Layout.fillHeight: true }
    }
}

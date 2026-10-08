import QtQuick
import QtQuick.Layouts

RowLayout {
    id: root
    spacing: 4

    QuietButton {
        text: app.langTick >= 0 ? app.label("seg_physical") : ""
        chosen: app.viewMode === "physical"
        onClicked: app.setViewMode("physical")
    }
    QuietButton {
        text: app.langTick >= 0 ? app.label("seg_virtual") : ""
        chosen: app.viewMode === "virtual"
        onClicked: app.setViewMode("virtual")
    }
}

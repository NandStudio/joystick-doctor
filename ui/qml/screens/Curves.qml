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
            text: app.langTick >= 0 ? app.label("curve_title") : ""
            color: theme.ink
            font.family: app.displayFamily
            font.pixelSize: 25
        }
        Text {
            text: app.langTick >= 0 ? app.label("curve_sub") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Text {
            visible: app.curveDetail.length > 0
            text: app.curveDetail
            color: theme.ink
            font.family: app.bodyFamily
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 18

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 220
                radius: theme.radiusCard
                color: theme.surface
                Canvas {
                    id: plot
                    anchors.fill: parent
                    anchors.margins: 18
                    property color axis: theme.stroke
                    property color curve: theme.ink
                    onAxisChanged: requestPaint()
                    onCurveChanged: requestPaint()
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        var pts = app.curvePoints
                        ctx.strokeStyle = axis
                        ctx.lineWidth = 1
                        ctx.beginPath()
                        ctx.moveTo(0, height)
                        ctx.lineTo(width, height)
                        ctx.moveTo(0, height)
                        ctx.lineTo(0, 0)
                        ctx.stroke()
                        if (!pts || pts.length < 2)
                            return
                        ctx.strokeStyle = curve
                        ctx.lineWidth = 2.75
                        ctx.lineJoin = "round"
                        ctx.lineCap = "round"
                        ctx.beginPath()
                        for (var i = 0; i < pts.length; i++) {
                            var x = (i / (pts.length - 1)) * width
                            var y = height - Math.max(0, Math.min(1, pts[i])) * height
                            if (i === 0)
                                ctx.moveTo(x, y)
                            else
                                ctx.lineTo(x, y)
                        }
                        ctx.stroke()
                    }
                    Connections {
                        target: app
                        function onCurveChanged() { plot.requestPaint() }
                    }
                    Component.onCompleted: requestPaint()
                }
                Text {
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.margins: 10
                    text: app.langTick >= 0 ? app.label("axis_in") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 12
                }
                Text {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.margins: 10
                    text: app.langTick >= 0 ? app.label("axis_out") : ""
                    color: theme.muted
                    font.family: app.bodyFamily
                    font.pixelSize: 12
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 280
                spacing: 10
                Text {
                    text: app.curveName
                    color: theme.ink
                    font.family: app.displayFamily
                    font.pixelSize: 17
                }
                QuietButton {
                    text: app.langTick >= 0 ? app.label("preset_linear") : ""
                    chosen: app.curvePreset === "linear"
                    onClicked: app.setCurvePreset("linear")
                }
                QuietButton {
                    text: app.langTick >= 0 ? app.label("preset_aggressive") : ""
                    chosen: app.curvePreset === "aggressive"
                    onClicked: app.setCurvePreset("aggressive")
                }
                QuietButton {
                    text: app.langTick >= 0 ? app.label("preset_smooth") : ""
                    chosen: app.curvePreset === "smooth"
                    onClicked: app.setCurvePreset("smooth")
                }
            }
        }

        Text {
            text: app.langTick >= 0 ? app.label("radial_note") : ""
            color: theme.muted
            font.family: app.bodyFamily
            font.pixelSize: 12
        }

        GridLayout {
            columns: 2
            columnSpacing: 18
            rowSpacing: 8
            Layout.fillWidth: true
            FieldSlider {
                caption: app.langTick >= 0 ? app.label("inner_label") : ""
                from: 0
                to: 90
                amount: app.innerPercent
                onMoved: function(amount) { app.setInner(amount) }
                Layout.fillWidth: true
            }
            FieldSlider {
                caption: app.langTick >= 0 ? app.label("outer_label") : ""
                from: 10
                to: 100
                amount: app.outerPercent
                onMoved: function(amount) { app.setOuter(amount) }
                Layout.fillWidth: true
            }
            FieldSlider {
                caption: app.langTick >= 0 ? app.label("trigger_inner_label") : ""
                from: 0
                to: 90
                amount: app.triggerInnerPercent
                onMoved: function(amount) { app.setTriggerInner(amount) }
                Layout.fillWidth: true
            }
            FieldSlider {
                caption: app.langTick >= 0 ? app.label("trigger_outer_label") : ""
                from: 10
                to: 100
                amount: app.triggerOuterPercent
                onMoved: function(amount) { app.setTriggerOuter(amount) }
                Layout.fillWidth: true
            }
        }

        RowLayout {
            spacing: 8
            InkButton {
                text: app.langTick >= 0 ? app.label("apply_virtual") : ""
                onClicked: app.applyCurve()
            }
            QuietButton {
                framed: true
                text: app.langTick >= 0 ? app.label("discard") : ""
                onClicked: app.discardCurve()
            }
        }
    }
}

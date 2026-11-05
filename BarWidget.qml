import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "koda"

  property bool menuOpen: false
  readonly property bool opened: menuOpen

  function open() {
    root.menuOpen = true
  }

  function close() {
    root.menuOpen = false
  }

  readonly property color foreground: bar ? bar.barForeground : Commons.Color.foreground
  readonly property color accent: Commons.Color.accent
  readonly property color popupBg: Commons.Color.popups.background
  readonly property color popupText: Commons.Color.popups.text
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property string statusScriptPath: decodeURIComponent(String(Qt.resolvedUrl("koda-status.py")).replace(/^file:\/\//, ""))

  Commons.Translations {
    id: strings
    directory: Qt.resolvedUrl("i18n")
  }

  property var statusData: ({
    ok: true,
    user: "Koda User",
    tier: "Free",
    tooltip_text: "Koda CLI",
    groups: []
  })
  property bool isDefaultAgent: false

  function refresh() {
    statusProcess.running = false
    statusProcess.running = true
    checkDefaultAgent()
  }

  function checkDefaultAgent() {
    checkAgentProcess.running = false
    checkAgentProcess.running = true
  }

  Process {
    id: launchProcess
    command: [
      "bash", "-lc",
      "if command -v omarchy-launch-tui >/dev/null 2>&1; then " +
      "  exec omarchy-launch-tui --app-id=org.omarchy.koda koda; " +
      "elif command -v xdg-terminal-exec >/dev/null 2>&1; then " +
      "  exec xdg-terminal-exec --app-id=org.omarchy.koda -e koda; " +
      "else " +
      "  exec koda; " +
      "fi"
    ]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: console.log("[Koda plugin] launch stdout: " + text)
    }
    stderr: StdioCollector {
      waitForEnd: true
      onStreamFinished: console.log("[Koda plugin] launch stderr: " + text)
    }
    onExited: function(exitCode) {
      console.log("[Koda plugin] launchProcess exited with code: " + exitCode)
    }
  }

  function launchKoda() {
    console.log("[Koda plugin] Launching Koda CLI agent...")
    launchProcess.running = false
    launchProcess.running = true
    root.close()
  }

  onMenuOpenChanged: {
    if (root.menuOpen) {
      if (!root.statusData || root.statusData.source !== "live") {
        root.refresh()
      }
    }
  }

  Timer {
    id: fastRetryTimer
    interval: 5000
    repeat: false
    running: false
    onTriggered: root.refresh()
  }

  Component.onCompleted: {
    refresh()
  }

  Timer {
    interval: 120000
    repeat: true
    running: true
    onTriggered: root.refresh()
  }

  Process {
    id: statusProcess
    command: [
      "python3",
      root.statusScriptPath,
      "--lang",
      Commons.I18n.language || "en"
    ]
    stdout: StdioCollector {
      id: statusCollector
      waitForEnd: true
      onStreamFinished: {
        try {
          var parsed = JSON.parse(text)
          if (parsed && typeof parsed === "object") {
            root.statusData = parsed
            if (parsed.source === "cache" || parsed.network_warning || !parsed.groups || parsed.groups.length < 2) {
              fastRetryTimer.start()
            }
          }
        } catch (e) {
          fastRetryTimer.start()
        }
      }
    }
  }

  Process {
    id: checkAgentProcess
    command: ["bash", "-c", "cat \"$HOME/.config/omarchy/defaults/agent\" 2>/dev/null || true"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var agent = String(text).trim()
        root.isDefaultAgent = (agent === "koda" || agent === "koda-cli")
      }
    }
  }

  ShellIpc {
    target: "koda"
    function toggle(): void { root.menuOpen = !root.menuOpen }
    function open(): void { root.menuOpen = true }
    function close(): void { root.menuOpen = false }
    function refresh(): void { root.refresh() }
    function launch(): void { root.launchKoda() }
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component {
    id: kodaIconComponent

    Image {
      id: kodaSvg
      fillMode: Image.PreserveAspectFit
      source: Qt.resolvedUrl("assets/koda.svg")
      sourceSize: Qt.size(48, 48)
      mipmap: true
      layer.enabled: true
      layer.effect: MultiEffect {
        colorization: 1.0
        colorizationColor: root.foreground
        opacity: root.isDefaultAgent ? 1.0 : 0.85
      }
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    iconComponent: kodaIconComponent
    tooltipText: (root.statusData && root.statusData.tooltip_text) ? root.statusData.tooltip_text : "Koda CLI"

    onPressed: function(b) {
      if (b === Qt.LeftButton) {
        root.menuOpen = !root.menuOpen
        if (root.menuOpen) root.refresh()
      } else if (b === Qt.RightButton) {
        root.launchKoda()
      }
    }
  }

  PopupCard {
    id: menuPopup
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.menuOpen
    padding: Style.space(12)
    borderColor: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.35)
    contentWidth: menuPopup.fittedContentWidth(Style.space(310))
    contentHeight: menuPopup.fittedContentHeight(mainColumn.implicitHeight, Style.space(480))

    Column {
      id: mainColumn
      width: parent.width
      spacing: Style.space(10)

      // 1. Header (Icon + Titles + Default Badge)
      Item {
        width: parent.width
        implicitHeight: Style.space(36)
        height: implicitHeight

        Row {
          anchors.fill: parent
          spacing: Style.space(10)

          Rectangle {
            width: Style.space(36)
            height: Style.space(36)
            radius: Style.space(8)
            color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.2)
            border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.5)
            border.width: 1

            Image {
              anchors.centerIn: parent
              width: Style.space(18)
              height: Style.space(18)
              source: Qt.resolvedUrl("assets/koda.svg")
              fillMode: Image.PreserveAspectFit
            }
          }

          Column {
            width: parent.width - Style.space(46)
            spacing: Style.space(2)
            anchors.verticalCenter: parent.verticalCenter

            Row {
              spacing: Style.space(6)
              Text {
                text: "Koda CLI"
                color: root.popupText
                font.family: root.fontFamily
                font.pixelSize: Style.font.title
                font.bold: true
              }

              Rectangle {
                visible: root.isDefaultAgent
                height: Style.space(16)
                width: defaultText.implicitWidth + Style.space(10)
                radius: Style.space(8)
                color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.25)

                Text {
                  id: defaultText
                  anchors.centerIn: parent
                  text: strings.t("badge.default", "Default")
                  color: root.accent
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.caption
                  font.bold: true
                }
              }
            }

            Text {
              text: (root.statusData.user || strings.t("user.default", "User")) + " · " + (root.statusData.tier || "Free") + " " + strings.t("tier.suffix", "Tier")
              color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.6)
              font.family: root.fontFamily
              font.pixelSize: Style.font.bodySmall
              elide: Text.ElideRight
              width: parent.width
            }
          }
        }
      }

      // Divider
      Rectangle {
        width: parent.width
        height: 1
        color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.1)
      }

      // 2. Model Groups Detail
      Column {
        width: parent.width
        spacing: Style.space(6)

        Repeater {
          model: (root.statusData && root.statusData.groups) ? root.statusData.groups : []

          Rectangle {
            width: mainColumn.width
            implicitHeight: groupCol.implicitHeight + Style.space(14)
            height: implicitHeight
            radius: Style.space(6)
            color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.03)

            Column {
              id: groupCol
              anchors.fill: parent
              anchors.margins: Style.space(7)
              spacing: Style.space(4)

              Item {
                width: parent.width
                implicitHeight: groupTitle.implicitHeight
                height: implicitHeight

                Text {
                  id: groupTitle
                  anchors.left: parent.left
                  text: modelData.name
                  color: root.popupText
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.bodySmall
                  font.bold: true
                }

                Text {
                  anchors.right: parent.right
                  text: modelData.remaining + " " + strings.t("limits.remaining", "left")
                  color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.85)
                  font.family: root.fontFamily
                  font.pixelSize: Style.font.bodySmall
                }
              }

              // Progress bar
              Rectangle {
                width: parent.width
                height: Style.space(4)
                radius: Style.space(2)
                color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.12)

                Rectangle {
                  height: parent.height
                  radius: Style.space(2)
                  color: (modelData.remaining <= 10) ? Commons.Color.urgent : root.accent
                  width: Math.max(2, parent.width * Math.min(1.0, Math.max(0.0, (modelData.remaining || 0) / (modelData.max || 1))))
                }
              }

              Text {
                visible: !!modelData.reset_text
                text: strings.t("limits.resets", "Resets:") + " " + modelData.reset_text
                color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.5)
                font.family: root.fontFamily
                font.pixelSize: Style.font.caption
              }
            }
          }
        }

        // Empty state / not authenticated fallback notice
        Rectangle {
          visible: !root.statusData.groups || root.statusData.groups.length === 0
          width: mainColumn.width
          implicitHeight: noGroupsCol.implicitHeight + Style.space(16)
          height: implicitHeight
          radius: Style.space(6)
          color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.04)

          Column {
            id: noGroupsCol
            anchors.fill: parent
            anchors.margins: Style.space(10)
            spacing: Style.space(4)

            Text {
              width: parent.width
              wrapMode: Text.Wrap
              text: root.statusData.authenticated ? strings.t("limits.no_limits", "No active quotas found") : strings.t("status.not_authenticated", "Authentication required (`koda`)")
              color: root.statusData.authenticated ? Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.75) : Commons.Color.urgent
              font.family: root.fontFamily
              font.pixelSize: Style.font.bodySmall
            }
          }
        }
      }

      // Divider
      Rectangle {
        width: parent.width
        height: 1
        color: Qt.rgba(root.popupText.r, root.popupText.g, root.popupText.b, 0.1)
      }

      // 3. Action Buttons
      Row {
        width: parent.width
        spacing: Style.space(6)

        Button {
          width: parent.width - Style.space(40)
          bordered: true
          foreground: root.accent
          iconText: "󰌑"
          text: strings.t("actions.launch", "Launch Koda")
          fontSize: Style.font.bodySmall
          onClicked: {
            root.launchKoda()
          }
        }

        Button {
          width: Style.space(34)
          bordered: true
          foreground: root.popupText
          iconText: "󰑐"
          iconSpinning: statusProcess.running
          tooltipText: strings.t("actions.refresh", "Refresh")
          onClicked: {
            console.log("[Koda plugin] Refresh button clicked")
            root.refresh()
          }
        }
      }
    }
  }
}

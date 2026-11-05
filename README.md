# Koda CLI — Omarchy Bar Plugin

[![Omarchy Plugin](https://img.shields.io/badge/Omarchy-Quattro%20Plugin-blue?style=flat-square)](https://plugins.omarchy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Koda CLI](https://img.shields.io/badge/Koda-CLI-orange?style=flat-square)](https://download.kodacode.ru)

A native status bar widget and quick-access panel for **Koda CLI** on **Omarchy Linux**. Monitor your model quotas in real time, view remaining limits, and launch the Koda AI coding agent with a single click.

---

## Features

- ⚡ **Real-Time Quota Tracking**: Instant breakdown of daily and monthly limits for Koda Base, Koda PRO, third-party models, and additional balance.
- 🔄 **Proactive Token Refresh**: Automatically refreshes authentication tokens in the background via Device Code so limits stay up to date without interrupting your workflow.
- 🚀 **One-Click Agent Launcher**: Launch Koda CLI inside Omarchy's floating terminal (`omarchy-launch-tui`) or default terminal.
- 🌐 **Multilingual (i18n)**: Automatically follows your system language configured in Omarchy settings (supports English and Russian out of the box).
- 🎨 **Adaptive Design**: Fully integrated with Omarchy theme palettes, typography, spacing, and accent colors.
- ⌨️ **IPC & Keybindings**: Control popup toggle, refresh, and launch from scripts or window manager shortcuts.

---

## Prerequisites & Installation

### 1. Install Koda CLI

Before using this plugin, ensure that **Koda CLI** is installed globally on your system.

According to the official [Koda Code Download Portal](https://download.kodacode.ru/), install it via npm:

```bash
npm i -g @kodadev/koda-cli
```

*(Ensure you have Node.js and npm installed)*.

### 2. Authenticate Koda CLI

Run the CLI once in your terminal to sign in:

```bash
koda
```

Follow the interactive login prompt. Once logged in, your credentials will be stored at `~/.config/koda/credentials.json`.

---

## Installing the Plugin in Omarchy

Install and enable the plugin directly using the Omarchy CLI:

```bash
omarchy plugin add https://github.com/Kowalski-coder/Koda-CLI-omarchy.git --enable
```

If you prefer to review before enabling:

```bash
omarchy plugin add https://github.com/Kowalski-coder/Koda-CLI-omarchy.git
omarchy plugin enable koda
```

---

## Uninstallation / Removal

To cleanly remove the plugin from your Omarchy system:

```bash
omarchy plugin remove koda
```

---

## Usage

- **Left-Click** on the Koda bar icon: Toggle the quota breakdown popup card.
- **Right-Click** on the Koda bar icon: Instantly launch Koda CLI in a terminal.
- **Refresh button (󰑐)** inside the panel: Force an immediate live quota refresh.
- **Launch button (󰌑)**: Open Koda CLI terminal session.

### Shell IPC Controls

You can trigger widget actions using Omarchy's Shell IPC:

```bash
# Toggle quota card
omarchy-shell koda toggle

# Open or close popup
omarchy-shell koda open
omarchy-shell koda close

# Force refresh limits
omarchy-shell koda refresh

# Launch Koda CLI terminal
omarchy-shell koda launch
```

### Keybinding Example (Hyprland)

Add this to `~/.config/hypr/hyprland.conf`:

```ini
# Toggle Koda CLI popup
bind = $mainMod, K, exec, omarchy-shell koda toggle
```

---

## Multilingual Support (i18n)

The plugin adheres to the Omarchy translation standard. It watches `~/.config/omarchy/language` and re-renders all interface texts dynamically whenever you switch your language in **Omarchy Settings > Setup > Language**.

- Default language catalogs are located in [`i18n/`](i18n/):
  - `en.json` (English)
  - `ru.json` (Russian)

To contribute or add another language (e.g., German, French, Spanish), simply create `i18n/<code>.json` matching your language code.

---

## Repository Structure

```
├── manifest.json       # Omarchy plugin contract and metadata
├── BarWidget.qml       # Main bar icon and interactive popup card
├── koda-status.py      # Background worker for quota fetching and token refresh
├── assets/
│   └── koda.svg        # Scalable vector icon
├── i18n/
│   ├── en.json         # English translation catalog
│   └── ru.json         # Russian translation catalog
├── LICENSE             # MIT License
└── README.md           # Documentation
```

---

## Validation

Verify the plugin integrity at any time with the Omarchy plugin validator:

```bash
omarchy plugin validate .
```

---

## License

This project is licensed under the [MIT License](LICENSE).
Koda CLI is developed and maintained by [Koda Code](https://kodacode.ru/).

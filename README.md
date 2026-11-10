[English](README.md) | [简体中文](README_CN.md)

# wdnapps_hdmi_processor

HDMI / PC-peripheral application plugin package for wdnwebui. It currently provides
1 card:

| Card id | Title | Description |
|---|---|---|
| `usb_hid` | Smart PC Control | Natural-language task loop: HDMI-IN grabs the current screen → the VLM emits an action → USB HID injects keyboard and mouse events |

Action semantics (click / type / key / hotkey / wait / done / not_found), converting
the model's 0-1000 square canvas into PC virtual-desktop pixels, and de-bar-dered
warnings are all handled in the main process at `cards/usb_hid/agent.py`; the model
only emits raw text (host design principle 6).

## What Form It Takes

**This is a wdnwebui plugin.** The card backend imports host services with
`from app.core.*` (`ComputeRegistry` and friends), plus two genuine external SDK
dependencies:

* `wdnhid` — USB HID gadget / `DigitizerWriter` (`0..32767` coordinate space)
* `wdnav` — HDMI-IN `VideoCapture` frame grabbing (RGA, not cv2)

## Prerequisite: the HID gadget must be running on the host first

This is not something this wheel can be responsible for — when the kernel-side gadget
is missing the card still loads and the UI still opens, but no action is ever actually
delivered to the PC (and the symptom is highly misleading: wrong model coordinates
and a missing gadget look identical, both amount to "clicked and nothing happened").
Run this at boot:

```bash
sudo bash <wdnwebui>/scripts/setup_usb_hid_gadget.sh
# check the UDC state
cat /sys/class/udc/*/state     # expected: configured
```

## Installation

The host repo root carries an `update_rkwhl.sh` that drives the four SDKs and the two
card plugin packages together. **Prefer running it** over manual pip:

```bash
cd <wdnwebui>
./update_rkwhl.sh                       # reinstall only what the git HEAD says changed
UPDATE_RKWHL_FORCE_REBUILD=1 ./update_rkwhl.sh   # force a full reinstall
```

This package is processed **after** `wdnhid` / `wdnav` — the usb_hid card imports
those two SDKs, so having them installed first keeps the errors in the log from
pointing at "an SDK that isn't installed yet", a false lead.

After installing, the script runs a card registration check
(`scripts/check_plugin_entrypoints.py`) confirming that the `"usb-hid"` entry point
resolves to the card directory, that the manifest `"id"` is character-for-character
identical, and that `static/` exists. This blocks the silent failure where pip
reports success all the way through, yet the host startup FATAL-skips this card.

Manual installation also works:

```bash
cd <wdnwebui>/.venv/src
git clone git@github.com:rockchip-wardner/wdnapps_hdmi_processor.git
pip install -e wdnapps_hdmi_processor
```

It installs into wdnwebui's venv, next to wdnai/wdnav/wdndds/wdnhid. The host picks
it up automatically on restart, with no host configuration to change.

## Adding a New Card

Create the directory following the layout of `cards/usb_hid/`, then register in **two**
places in `pyproject.toml`: the entry point `"usb-hid" 形式的卡 id =
"wdnapps_hdmi_processor.cards.<new-card>"` (the left side uses **hyphens** and must be
character-for-character identical to the `"id"` in `manifest.json`; writing the module
name with underscores makes registration fail silently), and `["manifest.json",
"static/*"]` in `package-data` (without it the static assets do not enter the wheel).

## License

Apache-2.0. See [LICENSE](LICENSE).

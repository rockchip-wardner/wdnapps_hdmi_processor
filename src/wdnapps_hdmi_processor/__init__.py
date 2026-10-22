"""``wdnapps_hdmi_processor`` —— wdnwebui 的 HDMI / 电脑外设类应用插件包。

提供 1 张卡片（通过 ``wdnwebui.cards`` entry point 暴露）：

* ``usb_hid`` —— 智能电脑控制

与 ``wdnapps_video_analyzer`` 一样，这是 wdnwebui 的插件而非独立应用：
卡片后端 import 宿主的 ``app.core.*``（ComputeRegistry 等），
并且依赖 ``wdnhid``（USB HID gadget / DigitizerWriter 绑定）与
``wdnav``（HDMI-IN 抓帧）两个 SDK。因此必须 ``pip install -e`` 到
wdnwebui 的 ``.venv/src/``，与 wdnai/wdnav/wdndds/wdnhid 平级。
"""
from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
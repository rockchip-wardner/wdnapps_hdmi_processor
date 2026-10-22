"""卡片集合（当前仅 ``usb_hid``）。

与 ``wdnapps_video_analyzer.cards`` 同理：不要在这里 import 具体卡片，
宿主 manifest 加载器按 entry point 逐个导入。
"""
from __future__ import annotations
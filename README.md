# wdnapps_hdmi_processor

wdnwebui 的 **HDMI / 电脑外设类应用插件包**。当前提供 1 张卡：

| 卡 id | 标题 | 说明 |
|---|---|---|
| `usb_hid` | 智能电脑控制 | 自然语言任务循环：HDMI-IN 抓当前画面 → VLM 出动作 → USB HID 注入键鼠 |

动作语义（click / type / key / hotkey / wait / done / not_found）、坐标从模型的
0-1000 方画布换算到 PC 虚拟桌面像素、以及去黑边后的告警，全部在主进程
`cards/usb_hid/agent.py` 里做；模型只吐原始文本（宿主设计原则 6）。

## 它是什么形态

**这是 wdnwebui 的插件。** 卡片后端 `from app.core.*` import 宿主服务
（`ComputeRegistry` 等），另有两个真·外部 SDK 依赖：

* `wdnhid` —— USB HID gadget / `DigitizerWriter`（`0..32767` 坐标域）
* `wdnav` —— HDMI-IN `VideoCapture` 抓帧（RGA，不走 cv2）

## 前置：HID gadget 必须先在主机上起来

这不是本 wheel 能负责的——内核侧 gadget 缺失时卡片能加载、UI 能开，但每一步动作
都不会真正下发到 PC（且症状极具迷惑性：模型坐标算错和 gadget 缺失表现一样，
都会"点了没反应"）。开机先跑：

```bash
sudo bash <wdnwebui>/scripts/setup_usb_hid_gadget.sh
# 确认 UDC 状态
cat /sys/class/udc/*/state     # 期望: configured
```

## 安装

```bash
cd <wdnwebui>/.venv/src
git clone git@10.10.10.10:wardner/wdnapps_hdmi_processor.git
pip install -e wdnapps_hdmi_processor
```

装到 wdnwebui 的 venv 里，与 wdnai/wdnav/wdndds/wdnhid 平级。宿主重启时自动发现，
无需改宿主配置。

## 加一张新卡

照 `cards/usb_hid/` 的结构建目录，然后在 `pyproject.toml` 注册**两处**：
entry point `"usb-hid" 形式的卡 id = "wdnapps_hdmi_processor.cards.<新卡>"`（左边用
**连字符**且须与 `manifest.json` 的 `"id"` 逐字相同，照着模块名下划线写会静默注册
失败），以及 `package-data` 里的 `["manifest.json", "static/*"]`（不加则静态资源
不进 wheel）。
# AGENTS.md

Quick reference for agent sessions in this repo.

HDMI / PC-peripheral application plugin package for `wdnwebui`. It
currently provides 1 card: `usb-hid` —— 把板子当成 PC 的 USB 外设
（键盘 / 鼠标 / digitizer）操作，底座是 `wdnhid`。

## 仓库地址与同步策略（2026-11-10）

| 角色 | 地址 | 允许的操作 |
|---|---|---|
| **局域网主仓库** | http://10.10.10.10:8080/wardner | **pull + push** —— 唯一权威源，所有更新的第一站 |
| **GitHub** | https://github.com/rockchip-wardner | **只允许 push** —— 发布镜像，不从它 pull |
| **Gitee 国内镜像** | https://gitee.com/rockchip-wardner | **不允许任何 git 操作** —— 公开只读镜像，内容由上游自动同步 |

远端命名：`origin` = `git@10.10.10.10:wardner/wdnapps_hdmi_processor.git`（局域网），
`github` = `git@github.com:rockchip-wardner/wdnapps_hdmi_processor.git`（只 push）。

**提交顺序不可颠倒：先 `git push origin master`（局域网主仓库），再
`git push github master`（GitHub）。Gitee 一概不碰。** `master` 的跟踪分支指向
`origin`，裸 `git pull` / `git push` 即为对主仓库操作。拉取最新代码只走局域网
主仓库 —— 从 GitHub 拉的是「已发布出去的历史」，会让本地与主仓库分叉。

## 提交信息规范（2026-11-11）

**commit message 必须用英文。**

- 格式：Conventional Commits —— `type(scope): subject`，正文（若有）也用英文。
  例：`feat(usb-hid): probe whether the kernel supports the HID gadget`
- 原因：本仓发布到公开的 GitHub 镜像（发布镜像 = 国际可见），提交历史是给国际读者
  看的 —— 中文提交信息让公开历史没法读。
- **只约束提交信息**：代码注释、docstring、仓内文档（AGENTS.md / README）仍按各仓
  现有的写法（中文没问题）。README 是中英双语，AGENTS.md 允许中文。


## Repo map (one-line each)

- `src/wdnapps_hdmi_processor/cards/usb_hid/` — the card: `manifest.json` + `api.py` / `service.py` / `agent.py` + `static/`.
- The host discovers the cards through the `wdnwebui.cards` entry point group —— `manifest.json` 是宿主装载的唯一契约。
- `src/wdnapps_hdmi_processor/__init__.py` — the package version.

### usb_hid agent：模型复读 JSON Schema 外壳时怎么活下来（2026-11-12）

Qwen3.5-9B 在**真·非思考模式**下会**复读提示里的 JSON Schema 外壳** ——
把 `model_json_schema()` 的结构原样抄回来，只把值填进去：

```` ```json
{"properties": {"action": "key", "x": null, …, "text": "notepad",
                "thought": "…"}}
``` ````

这不是合法的 schema 实例 → pydantic 校验失败 → wdnai 的 `_safe_validate`
把它降级成「**只带 `text` 字段的实例**」→ `model_dump()` 里**根本没有
`action` 键** → agent 拿到一个没有动作的 dict，报「不支持的动作: ''」，
整轮电脑控制全废。

⇒ `_coerce_action` 在 `isinstance(result, AgentAction)` 这条分支上多了一步：
**实例里没有 `action` 时，拿 `self._last_raw`（`on_delta` 收回的原始文本）
再解析一次**。`_parse_action_json` / `_normalize_action` 本来就认识
`{"properties": {...}}` 这层外壳（`_normalize_action` 里那句
`if "action" not in body and isinstance(body.get("properties"), dict)`），
只是原来**走不到** —— wdnai 把原文吞了，只留下一个残缺的实例。

教训：**别信「`respond(generating=…)` 返回了 schema 实例」就等于解析成功。**
校验失败时它可能是个只有 `text` 的空壳，真正的内容在原始文本里。

> ⚠️ 补记（当天晚些时候）：上面说的「复读 schema 外壳」，**根因其实是
> C 会话被上一轮请求污染**（9B 的会话级 `keep_history=1`，跨请求累积）。
> KV 干净之后，模型自己就吐正常 JSON 了。所以这段兜底现在是**保险**，
> 不是主路径 —— 但仍然要留着（模型偶尔也会自己复读）。

### usb_hid agent：点击坐标为什么偏（2026-11-12）

用户报「点击坐标又偏移了」。这一轮查下来有**两层**原因，别混：

**第一层：C 会话跨请求累积 → 模型在回答上一轮的问题。**
9B 的会话级 `keep_history=1`（vendor 写死），而这个后端自己拼完整 ChatML
prompt、不依赖会话历史。实测：让 9B「点击任务栏最左边的 Windows 开始按钮」，
它 thought 里写的却是**上一轮**「打开记事本」的目标，坐标也照着上一轮给。
⇒ 修在 **worker**（`wdnwebui/app/core/compute/workers/_base.py` 里给每个
请求带 `keep_history=False`），不在 agent —— 详见 wdnwebui 的 AGENTS.md
「C 会话不能跨请求累积上下文」那条。

**第二层：9B 的视觉塔只有 384×384，小图标定位本来就不可靠。**
1920 宽的桌面进去只剩 384 宽，任务栏上一个个图标只有 10 px 宽。同一张图、
同一段提示问「最左边的开始按钮」，落点在实测里从**差 11 px**到**差 116 px**
都有（同一张图重复问，答案还会跳）。⇒ 粗定位只能用来**圈定邻域**。

⇒ **放大精修**（`_refine_point`）：粗落点附近 320×200 的**原图**裁下来
（不是缩放后的画布！），letterbox 成正方形再问一次，落点按裁剪区的 meta
换算回去。实测误差 **92 px → 24 px**（图标本身 44 px 宽，24 px 落在图标内）。
- 窗口大小是权衡：320×200 实测最好（640×400 → 45 px，240×150 → 34 px）。
  太小了模型在放大图里认不出目标。
- 裁剪区**压扁**（无灰边）反而更差（37 px vs 24 px），保持 letterbox。
- 失败（模型不给坐标 / 换了动作 / 抛异常）就**保留粗落点** —— 只会更准，
  不会更差。
- 代价：每个点击动作多一次推理（一步 ~8 s → ~11 s）。

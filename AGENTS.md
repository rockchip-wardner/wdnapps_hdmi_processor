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

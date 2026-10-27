# MaiBot Discord 适配器插件 (Discord Adapter)

[![MaiBot Plugin SDK](https://img.shields.io/badge/MaiBot%20SDK-v2.0+-blue.svg)](https://docs.maibot.chat)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)

专为 [MaiBot (麦麦)](https://github.com/Mai-with-u/MaiBot) 打造的现代化、高可用 **Discord 双工消息网关适配器**。通过 Discord 官方 Bot API 直连，彻底摆脱手机端容器、协议逆向和风控下线的烦恼。

---

## ✨ 核心特性

- **官方原生接入，零风控永不掉线**：基于 Discord 官方 WebSocket Gateway 与 REST API，无需手机或模拟器，无需扫码，无任何封号风控。
- **双工消息网关 (Duplex Gateway)**：严格遵循 MaiBot SDK 2.x `@MessageGateway` 规范，支持入站消息注入与出站回复路由。
- **全场景会话支持**：
  - **私聊 (Direct Message)**：像真人微信/QQ一样一对一直接交流。
  - **服务器频道 (Guild Channel)**：群聊交流，支持自由发言或通过 `@机器人` 触发。
- **多媒体与富交互**：
  - 支持文本、图片、附件、Sticker 贴纸识别。
  - 支持 Discord 消息引用回复（Reply Quote）。
  - 支持 Discord 2000 字符上限智能分段发送，避免截断或发送失败。
  - 支持“正在输入中...”状态提示（Typing Indicator）。
- **细粒度过滤与权限**：支持私聊开关、频道白名单/黑名单、用户黑名单。
- **轻量低开销**：纯异步 Python 库（`discord.py`），常驻内存仅数十兆，非常适合海外 VPS / 低配服务器。

---

## 🚀 准备工作：创建 Discord Bot

接入 Discord 机器人完全是官方合法流程，只需三步：

### 1. 创建 Application 并获取 Token
1. 浏览器打开 [Discord Developer Portal](https://discord.com/developers/applications)；
2. 点击右上角 **New Application**，输入机器人名称（例如 `小蓝`）；
3. 在左侧菜单点击 **Bot**，点击 **Reset Token** 生成并复制你的 **Bot Token**（妥善保管，切勿泄露）。

### 2. 开启必要权限开关 (Intents)
在 Bot 配置页面向下滚动到 **Privileged Gateway Intents**，务必将以下开关点亮打开：
- ✅ **Presence Intent**
- ✅ **Server Members Intent**
- ✅ **Message Content Intent**（核心：允许机器人读取消息正文）

保存修改（Save Changes）。

### 3. 生成邀请链接拉入你的服务器
1. 点击左侧 **OAuth2** → **URL Generator**；
2. 在 **SCOPES** 区域勾选：`bot`；
3. 在下方出现的 **BOT PERMISSIONS** 区域勾选：
   - `Send Messages`
   - `Read Message History`
   - `Attach Files`
   - `Embed Links`
   - `View Channels`
4. 复制页面最底部生成的链接，在浏览器中打开，选择将 Bot 添加到你的 Discord 服务器中。

---

## 📦 安装与配置

### 方式 A：通过 WebUI 插件市场安装（推荐）
1. 打开 MaiBot WebUI → **插件管理** → **插件市场**；
2. 搜索 `Discord 适配器` 并点击安装；
3. 安装完成后，在已安装插件列表中点击设置，填入第 1 步获取的 `token`，保存并重启麦麦即可。

### 方式 B：手动克隆安装
进入麦麦实例目录：
```bash
cd /opt/maibot/instance/plugins/
git clone https://github.com/WiseXin/MaiBot-Discord-Adapter.git maibot-discord-adapter
```
安装依赖：
```bash
pip install "discord.py>=2.3.0"
```
重启 MaiBot 后即可在 WebUI 中看到该插件。

---

## ⚙️ 配置说明

插件配置文件为 `config.toml`，也可在 WebUI 中可视化修改：

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `token` | `str` | `""` | **必填**。从 Discord 开发者后台获取的 Bot Token |
| `allow_dm` | `bool` | `true` | 是否允许在 Discord 私聊(DM)中与麦麦对话 |
| `require_mention_in_guild` | `bool` | `false` | 在服务器频道中是否必须@机器人；设为 `true` 可防止群聊刷屏 |
| `channel_whitelist` | `list[str]` | `[]` | 频道白名单（填 Channel ID）；留空表示允许全部频道 |
| `channel_blacklist` | `list[str]` | `[]` | 频道黑名单；忽略这些频道的所有消息 |
| `user_blacklist` | `list[str]` | `[]` | 用户黑名单（填 User ID）；忽略这些用户 |
| `send_typing_indicator` | `bool` | `true` | 发送回复前是否展示“正在输入中...”状态 |

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎提交 PR 和 Issue！

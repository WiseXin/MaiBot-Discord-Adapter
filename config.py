"""Discord 适配器配置模型。

定义插件的运行时配置结构，支持 WebUI 表单渲染、结构校验与配置热重载。
遵循 MaiBot SDK 2.x 配置模型规范，包含 [plugin] 基础配置节与 [bot] 连接配置节。
"""

from typing import Any, ClassVar, List
from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator


class PluginSectionConfig(PluginConfigBase):
    """插件基础配置节。"""

    __ui_label__: ClassVar[str] = "基础设置"
    __ui_icon__: ClassVar[str] = "settings"
    __ui_order__: ClassVar[int] = 0

    enabled: bool = Field(default=True, description="是否启用 Discord 适配器")
    config_version: str = Field(default="1.0.0", description="当前配置结构版本")


class DiscordBotConfig(PluginConfigBase):
    """Discord 平台连接与过滤配置节。"""

    __ui_label__: ClassVar[str] = "Discord 机器人设置"
    __ui_icon__: ClassVar[str] = "bot"
    __ui_order__: ClassVar[int] = 1

    token: str = Field(
        default="",
        description="Discord Bot Token，在 Discord Developer Portal -> Bot 页面获取",
    )

    allow_dm: bool = Field(
        default=True,
        description="是否允许在 Discord 私聊(DM)中与麦麦对话",
    )

    require_mention_in_guild: bool = Field(
        default=False,
        description="在服务器频道中是否必须@麦麦才触发回复；私聊不受此限制",
    )

    channel_whitelist: List[str] = Field(
        default_factory=list,
        description="频道白名单：允许交互的 Discord 频道 ID 列表；留空表示允许所有未被加入黑名单的频道",
    )

    channel_blacklist: List[str] = Field(
        default_factory=list,
        description="频道黑名单：忽略这些 Discord 频道的任何消息",
    )

    user_blacklist: List[str] = Field(
        default_factory=list,
        description="用户黑名单：忽略这些 Discord 用户的任何消息",
    )

    send_typing_indicator: bool = Field(
        default=True,
        description="回复前是否在 Discord 频道显示'正在输入中...'提示",
    )


class DiscordAdapterConfig(PluginConfigBase):
    """Discord 平台适配器完整配置模型。"""

    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    bot: DiscordBotConfig = Field(default_factory=DiscordBotConfig)

    @model_validator(mode="before")
    @classmethod
    def _migrate_and_nest_config(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 保证 plugin 节点及 config_version 存在
            plugin_dict = data.get("plugin")
            if not isinstance(plugin_dict, dict):
                data["plugin"] = {"enabled": True, "config_version": "1.0.0"}
            elif not plugin_dict.get("config_version"):
                plugin_dict["config_version"] = "1.0.0"

            # 兼容扁平顶层字段
            bot_dict = data.setdefault("bot", {})
            if isinstance(bot_dict, dict):
                for key in (
                    "token",
                    "allow_dm",
                    "require_mention_in_guild",
                    "channel_whitelist",
                    "channel_blacklist",
                    "user_blacklist",
                    "send_typing_indicator",
                ):
                    if key in data and key not in bot_dict:
                        bot_dict[key] = data[key]
        return data

    # 快捷属性访问代理
    @property
    def token(self) -> str:
        return self.bot.token

    @property
    def allow_dm(self) -> bool:
        return self.bot.allow_dm

    @property
    def require_mention_in_guild(self) -> bool:
        return self.bot.require_mention_in_guild

    @property
    def channel_whitelist(self) -> List[str]:
        return self.bot.channel_whitelist

    @property
    def channel_blacklist(self) -> List[str]:
        return self.bot.channel_blacklist

    @property
    def user_blacklist(self) -> List[str]:
        return self.bot.user_blacklist

    @property
    def send_typing_indicator(self) -> bool:
        return self.bot.send_typing_indicator

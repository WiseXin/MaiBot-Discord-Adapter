"""Discord 适配器配置模型。

定义插件的运行时配置结构，支持 WebUI 表单渲染与配置热重载。
"""

from typing import ClassVar, List
from maibot_sdk import Field, PluginConfigBase


class DiscordAdapterConfig(PluginConfigBase):
    """Discord 平台适配器配置项。"""

    __ui_label__: ClassVar[str] = "Discord 适配器设置"
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

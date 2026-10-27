"""Discord 双工平台消息网关适配器主入口。

实现 MaiBotPlugin 与 @MessageGateway，将 Discord 平台的私聊与频道消息
无缝接入麦麦统一消息管线，同时负责处理 Host 的出站回复。
"""

import asyncio
from typing import Any, ClassVar, Dict, Optional
import discord

from maibot_sdk import MaiBotPlugin, MessageGateway, PluginConfigBase

try:
    from .client import DiscordGatewayClient
    from .discord_codecs import discord_message_to_host, parse_host_outbound_message
    from .config import DiscordAdapterConfig
    from .constants import DEFAULT_SCOPE, GATEWAY_NAME, PLATFORM_NAME, PROTOCOL_NAME
except ImportError:
    from client import DiscordGatewayClient
    from discord_codecs import discord_message_to_host, parse_host_outbound_message
    from config import DiscordAdapterConfig
    from constants import DEFAULT_SCOPE, GATEWAY_NAME, PLATFORM_NAME, PROTOCOL_NAME


class DiscordAdapterPlugin(MaiBotPlugin):
    """Discord 双工平台适配器插件。"""

    config_model: ClassVar[type[PluginConfigBase] | None] = DiscordAdapterConfig

    def __init__(self) -> None:
        super().__init__()
        self._client: Optional[DiscordGatewayClient] = None
        self._runner_task: Optional[asyncio.Task] = None
        self._bot_user: Optional[discord.User] = None
        self._is_gateway_ready: bool = False
        self._user_dm_map: Dict[str, str] = {}

    async def on_load(self) -> None:
        """插件加载生命周期回调。"""
        self.ctx.logger.info("正在加载 Discord 平台适配器...")
        config: DiscordAdapterConfig = self.config  # type: ignore

        if not config.token or not config.token.strip():
            self.ctx.logger.warning(
                "【Discord 适配器】未检测到有效 token！请前往 WebUI 插件设置或 config.toml "
                "中填入 Discord Bot Token，保存后重启或等待连接。"
            )
            try:
                await self.ctx.gateway.update_state(
                    gateway_name=GATEWAY_NAME,
                    ready=False,
                    platform=PLATFORM_NAME,
                    reason="未检测到有效 token (Discord token is not configured)",
                )
            except Exception:
                pass
            return

        await self._start_client(config)

    async def on_unload(self) -> None:
        """插件卸载生命周期回调。"""
        self.ctx.logger.info("正在卸载 Discord 平台适配器...")
        await self._stop_client()
        self.ctx.logger.info("Discord 平台适配器已卸载并下线。")

    async def on_config_update(
        self, scope: str, config_data: Dict[str, Any], version: str
    ) -> None:
        """配置热更新回调。"""
        del scope, version
        self.ctx.logger.info("收到 Discord 适配器配置更新通知，正在重载...")
        config: DiscordAdapterConfig = self.config  # type: ignore

        # 若 Token 发生变更，重启 Discord Client 连接
        if self._client is not None:
            old_token = getattr(self._client.config, "token", "")
            if old_token != config.token:
                self.ctx.logger.info("检测到 Token 发生变更，正在重新建立 Discord 连接...")
                await self._stop_client()
                if config.token and config.token.strip():
                    await self._start_client(config)
            else:
                # 仅更新过滤规则与行为配置
                self._client.config = config
                self.ctx.logger.info("Discord 适配器运行时过滤参数已热生效。")
        elif config.token and config.token.strip():
            await self._start_client(config)

    # ==================== 核心网关组件 ====================

    @MessageGateway(
        route_type="duplex",
        name=GATEWAY_NAME,
        platform=PLATFORM_NAME,
        protocol=PROTOCOL_NAME,
    )
    async def handle_discord_gateway(
        self,
        message: Dict[str, Any],
        route: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """出站：接收 Host 消息并转发到对应的 Discord 频道或私聊。"""
        del metadata, kwargs

        if self._client is None or self._client.is_closed() or not self._is_gateway_ready:
            return {
                "success": False,
                "error": "Discord 网关客户端尚未就绪或已断开",
            }

        try:
            bot_id_str = str(self._bot_user.id) if self._bot_user else None
            channel_id, user_id, text, image_urls, reply_to = parse_host_outbound_message(
                message, route=route, bot_id=bot_id_str
            )
            self.ctx.logger.info(
                "Discord 出站解析完成: channel_id=%s, user_id=%s, text_len=%d, text_preview=%r",
                channel_id,
                user_id,
                len(text),
                text[:60] if text else "",
            )

            # 兜底查找缓存：若私聊出站未直接拿到 channel_id，通过 user_id 反查 DM 频道
            if not channel_id and user_id and user_id in self._user_dm_map:
                channel_id = self._user_dm_map[user_id]

            sent_msgs = await self._client.send_to_channel_or_user(
                channel_id=channel_id,
                user_id=user_id,
                text=text,
                image_urls=image_urls,
                reply_to_id=reply_to,
            )

            external_id = str(sent_msgs[0].id) if sent_msgs else ""
            return {
                "success": True,
                "external_message_id": external_id,
            }
        except Exception as exc:
            self.ctx.logger.error("发送 Discord 消息失败: %s", exc, exc_info=True)
            return {
                "success": False,
                "error": str(exc),
            }

    # ==================== 内部状态与事件管理 ====================

    async def _handle_discord_ready(self, bot_user: discord.User) -> None:
        """Discord 登录就绪，向 Host 注册网关就绪态。"""
        self._bot_user = bot_user
        account_id_str = str(bot_user.id)

        # 向上汇报网关已就绪
        await self.ctx.gateway.update_state(
            gateway_name=GATEWAY_NAME,
            ready=True,
            platform=PLATFORM_NAME,
            account_id=account_id_str,
            scope=DEFAULT_SCOPE,
            metadata={
                "protocol": PROTOCOL_NAME,
                "bot_name": bot_user.name,
                "bot_id": account_id_str,
            },
        )
        self._is_gateway_ready = True
        self.ctx.logger.info(
            "【Discord 网关就绪】账号 ID: %s (%s) 状态: 已上线",
            account_id_str,
            bot_user.name,
        )

    async def _handle_discord_inbound(self, message: discord.Message) -> None:
        """入站：收到 Discord 消息，打包并注入 Host 消息管线。"""
        if not self._is_gateway_ready or self._bot_user is None:
            self.ctx.logger.warning("网关尚未完成握手，忽略入站消息")
            return

        # 若是私聊消息，缓存 author_id -> DM channel_id 映射
        if message.guild is None:
            self._user_dm_map[str(message.author.id)] = str(message.channel.id)

        bot_account_id = str(self._bot_user.id)
        host_payload = await discord_message_to_host(message, bot_account_id)
        msg_id_str = str(message.id)

        accepted = await self.ctx.gateway.route_message(
            gateway_name=GATEWAY_NAME,
            message=host_payload,
            external_message_id=msg_id_str,
            dedupe_key=f"discord_{msg_id_str}",
        )

        if not accepted:
            self.ctx.logger.debug(
                "Discord 入站消息被 Host 路由策略拦截或未处理: msg_id=%s",
                msg_id_str,
            )

    async def _start_client(self, config: DiscordAdapterConfig) -> None:
        """启动 Discord 客户端异步常驻任务。"""
        token_clean = config.token.strip()
        self._client = DiscordGatewayClient(
            config=config,
            on_ready_cb=self._handle_discord_ready,
            on_inbound_cb=self._handle_discord_inbound,
            enable_message_content=True,
        )

        async def _client_runner():
            try:
                self.ctx.logger.info("正在连接 Discord Gateway...")
                await self._client.start(token_clean)
            except discord.errors.PrivilegedIntentsRequired:
                self.ctx.logger.warning(
                    "【Discord 提示】检测到开发者后台未开启 Privileged Intents (Message Content Intent)。"
                    "正在自动降级为标准模式连接（私聊与@提及均可正常使用）..."
                )
                self._client = DiscordGatewayClient(
                    config=config,
                    on_ready_cb=self._handle_discord_ready,
                    on_inbound_cb=self._handle_discord_inbound,
                    enable_message_content=False,
                )
                try:
                    await self._client.start(token_clean)
                except Exception as exc:
                    self.ctx.logger.error("Discord 降级模式客户端运行异常: %s", exc, exc_info=True)
            except asyncio.CancelledError:
                pass
            except discord.LoginFailure:
                self.ctx.logger.error("【Discord 登录失败】提供的 Token 无效或已被重置！")
            except Exception as exc:
                self.ctx.logger.error("Discord 客户端运行异常: %s", exc, exc_info=True)
            finally:
                if self._is_gateway_ready:
                    await self._notify_gateway_offline()

        self._runner_task = asyncio.create_task(_client_runner())

    async def _stop_client(self) -> None:
        """停止 Discord 客户端并注销网关。"""
        await self._notify_gateway_offline()

        if self._client is not None and not self._client.is_closed():
            try:
                await self._client.close()
            except Exception as exc:
                self.ctx.logger.warning("关闭 Discord 客户端异常: %s", exc)

        if self._runner_task is not None and not self._runner_task.done():
            self._runner_task.cancel()
            try:
                await asyncio.wait_for(self._runner_task, timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        self._client = None
        self._runner_task = None
        self._bot_user = None

    async def _notify_gateway_offline(self) -> None:
        """通知 Host 网关离线。"""
        if self._is_gateway_ready:
            self._is_gateway_ready = False
            try:
                await self.ctx.gateway.update_state(
                    gateway_name=GATEWAY_NAME,
                    ready=False,
                    platform=PLATFORM_NAME,
                )
            except Exception as exc:
                self.ctx.logger.warning("更新网关离线状态异常: %s", exc)


def create_plugin() -> DiscordAdapterPlugin:
    """插件工厂函数（MaiBot 宿主统一调用）。"""
    return DiscordAdapterPlugin()

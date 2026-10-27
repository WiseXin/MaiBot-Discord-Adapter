"""Discord.py 异步客户端封装与生命周期管理。"""

import asyncio
import logging
from typing import Callable, Coroutine, List, Optional
import discord

try:
    from .discord_codecs import split_text_into_chunks
    from .config import DiscordAdapterConfig
except ImportError:
    from discord_codecs import split_text_into_chunks
    from config import DiscordAdapterConfig

LOGGER = logging.getLogger("discord_adapter.client")


class DiscordGatewayClient(discord.Client):
    """继承自 discord.Client 的事件处理与出入站转发客户端。"""

    def __init__(
        self,
        config: DiscordAdapterConfig,
        on_ready_cb: Callable[[discord.User], Coroutine[None, None, None]],
        on_inbound_cb: Callable[[discord.Message], Coroutine[None, None, None]],
        *args,
        **kwargs,
    ) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.dm_messages = True
        intents.guild_messages = True
        intents.message_content = True  # 需要在 Discord 开发者后台开启

        super().__init__(intents=intents, *args, **kwargs)
        self.config = config
        self.on_ready_cb = on_ready_cb
        self.on_inbound_cb = on_inbound_cb
        self._is_ready_fired = False

    async def on_ready(self) -> None:
        """Discord 登录成功回调。"""
        LOGGER.info(
            "Discord Client 已成功登录: %s#%s (ID: %s)",
            self.user.name,
            self.user.discriminator,
            self.user.id,
        )
        self._is_ready_fired = True
        try:
            await self.on_ready_cb(self.user)
        except Exception as exc:
            LOGGER.error("on_ready 回调触发失败: %s", exc, exc_info=True)

    async def on_message(self, message: discord.Message) -> None:
        """收到 Discord 消息事件。"""
        # 1. 忽略自身或机器人发送的消息
        if message.author == self.user or message.author.bot:
            return

        user_id_str = str(message.author.id)
        channel_id_str = str(message.channel.id)

        # 2. 用户黑名单过滤
        if user_id_str in self.config.user_blacklist:
            LOGGER.debug("忽略黑名单用户消息: %s", user_id_str)
            return

        # 3. 私聊(DM)处理
        if message.guild is None:
            if not self.config.allow_dm:
                LOGGER.debug("私聊未开启，已跳过用户 %s 的消息", user_id_str)
                return
        else:
            # 4. 服务器频道黑白名单过滤
            if channel_id_str in self.config.channel_blacklist:
                LOGGER.debug("忽略黑名单频道消息: %s", channel_id_str)
                return

            if self.config.channel_whitelist and channel_id_str not in self.config.channel_whitelist:
                LOGGER.debug("频道 %s 未在白名单中，跳过", channel_id_str)
                return

            # 5. @提及要求过滤
            if self.config.require_mention_in_guild:
                if self.user not in message.mentions:
                    LOGGER.debug("频道消息未@机器人，跳过")
                    return

        # 6. 转交入站处理
        try:
            await self.on_inbound_cb(message)
        except Exception as exc:
            LOGGER.error("处理入站消息异常: %s", exc, exc_info=True)

    async def send_to_channel_or_user(
        self,
        channel_id: Optional[str],
        user_id: Optional[str],
        text: str,
        image_urls: List[str],
        reply_to_id: Optional[str] = None,
    ) -> List[discord.Message]:
        """将消息发送给指定的 Discord 频道或用户。"""
        destination = None

        if channel_id:
            try:
                destination = self.get_channel(int(channel_id))
                if destination is None:
                    destination = await self.fetch_channel(int(channel_id))
            except Exception as exc:
                LOGGER.warning("获取频道 %s 失败: %s", channel_id, exc)

        if destination is None and user_id:
            try:
                user = await self.fetch_user(int(user_id))
                destination = await user.create_dm()
            except Exception as exc:
                LOGGER.error("创建私聊会话失败 (用户: %s): %s", user_id, exc)

        if destination is None:
            raise ValueError(f"无法定位发送目标: channel_id={channel_id}, user_id={user_id}")

        # 尝试显示输入中状态
        if self.config.send_typing_indicator and hasattr(destination, "typing"):
            try:
                await destination.typing()
            except Exception:
                pass

        # 处理引用回复目标
        reference_msg = None
        if reply_to_id and hasattr(destination, "fetch_message"):
            try:
                reference_msg = await destination.fetch_message(int(reply_to_id))
            except Exception:
                pass

        sent_messages: List[discord.Message] = []

        # 按 2000 字符切分安全发送
        chunks = split_text_into_chunks(text) if text else [""]

        for idx, chunk in enumerate(chunks):
            # 仅首条消息附带引用回复
            ref = reference_msg if idx == 0 else None

            # 处理图片附件 Embed (若有图片链接)
            embeds = []
            if idx == len(chunks) - 1 and image_urls:
                for img_url in image_urls[:10]:
                    embed = discord.Embed()
                    embed.set_image(url=img_url)
                    embeds.append(embed)

            if chunk or embeds:
                msg = await destination.send(
                    content=chunk if chunk else None,
                    reference=ref,
                    embeds=embeds if embeds else None,
                )
                sent_messages.append(msg)

        return sent_messages

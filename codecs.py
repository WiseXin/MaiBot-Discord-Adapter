"""Discord 与 MaiBot 宿主消息格式双向编解码器。"""

from typing import Any, Dict, List, Optional, Tuple
import discord
from .constants import DEFAULT_SCOPE, MAX_DISCORD_MESSAGE_LENGTH, PLATFORM_NAME


def discord_message_to_host(
    discord_msg: discord.Message,
    bot_account_id: str,
) -> Dict[str, Any]:
    """将 Discord 原生 Message 对象转换为 MaiBot 标准 MessageDict 格式。"""
    segments: List[Dict[str, Any]] = []

    # 1. 提取引用回复 (Reply Quote)
    if discord_msg.reference and discord_msg.reference.message_id:
        segments.append({
            "type": "reply",
            "data": str(discord_msg.reference.message_id),
        })

    # 2. 提取正文文本
    clean_text = discord_msg.clean_content.strip()
    if clean_text:
        segments.append({
            "type": "text",
            "data": clean_text,
        })

    # 3. 提取附件（图片、文件）
    for attachment in discord_msg.attachments:
        content_type = getattr(attachment, "content_type", "") or ""
        if content_type.startswith("image/"):
            segments.append({
                "type": "image",
                "data": attachment.url,
            })
        else:
            segments.append({
                "type": "file",
                "data": attachment.url,
                "name": attachment.filename,
            })

    # 构造 group_info（群聊/频道信息）
    group_info: Optional[Dict[str, Any]] = None
    if discord_msg.guild:
        channel_name = getattr(discord_msg.channel, "name", "Guild Channel")
        group_info = {
            "platform": PLATFORM_NAME,
            "group_id": str(discord_msg.channel.id),
            "group_name": f"{discord_msg.guild.name}#{channel_name}",
        }

    return {
        "message_id": str(discord_msg.id),
        "platform": PLATFORM_NAME,
        "account_id": str(bot_account_id),
        "scope": DEFAULT_SCOPE,
        "timestamp": str(discord_msg.created_at.timestamp()),
        "message_info": {
            "user_info": {
                "platform": PLATFORM_NAME,
                "user_id": str(discord_msg.author.id),
                "user_nickname": discord_msg.author.display_name or discord_msg.author.name,
            },
            "group_info": group_info,
            "additional_config": {
                "guild_id": str(discord_msg.guild.id) if discord_msg.guild else "",
                "channel_id": str(discord_msg.channel.id),
                "is_dm": discord_msg.guild is None,
            },
        },
        "raw_message": segments if segments else [{"type": "text", "data": ""}],
    }


def split_text_into_chunks(text: str, max_length: int = MAX_DISCORD_MESSAGE_LENGTH) -> List[str]:
    """按字符上限安全分块文本，避免触发 Discord 2000 字符限制。"""
    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    lines = text.split("\n")
    for line in lines:
        line_len = len(line) + 1  # 计入换行符
        if current_len + line_len > max_length:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            # 单行依然超长则硬截断
            while len(line) > max_length:
                chunks.append(line[:max_length])
                line = line[max_length:]
            if line:
                current_chunk.append(line)
                current_len = len(line)
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def parse_host_outbound_message(
    host_msg: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str], str, List[str], Optional[str]]:
    """解析 Host 出站消息。

    Returns:
        (target_channel_id, target_user_id, text_content, image_urls, reply_to_message_id)
    """
    msg_info = host_msg.get("message_info") or {}
    group_info = msg_info.get("group_info") or {}
    user_info = msg_info.get("user_info") or {}
    add_cfg = msg_info.get("additional_config") or {}

    channel_id = str(group_info.get("group_id") or add_cfg.get("channel_id") or "").strip() or None
    user_id = str(user_info.get("user_id") or "").strip() or None

    text_parts: List[str] = []
    image_urls: List[str] = []
    reply_to: Optional[str] = None

    raw_msg = host_msg.get("raw_message") or []
    if isinstance(raw_msg, str):
        text_parts.append(raw_msg)
    elif isinstance(raw_msg, list):
        for seg in raw_msg:
            if not isinstance(seg, dict):
                continue
            stype = seg.get("type")
            sdata = seg.get("data")
            if stype == "text":
                text_parts.append(str(sdata or ""))
            elif stype == "image":
                if isinstance(sdata, str) and sdata.startswith("http"):
                    image_urls.append(sdata)
            elif stype == "reply":
                reply_to = str(sdata or "")

    return channel_id, user_id, "".join(text_parts), image_urls, reply_to

from __future__ import annotations
import asyncio
import os
import re
import tempfile
from contextlib import suppress

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.utils.chat_action import ChatActionSender
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
import logging
from yt_dlp import YoutubeDL


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = Router()


URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)


def extract_first_url(text: str | None) -> str | None:
    if not text:
        return None
    match = URL_REGEX.search(text)
    return match.group(0) if match else None


def is_supported_link(url: str) -> bool:
    url_lower = url.lower()
    is_tiktok = "tiktok.com" in url_lower
    is_instagram_reel = ("instagram.com" in url_lower) and ("/reel/" in url_lower or "/reels/" in url_lower)
    is_youtube_shorts = ("youtube.com/shorts" in url_lower) or ("youtu.be/" in url_lower)
    return is_tiktok or is_instagram_reel or is_youtube_shorts


def get_human_name(message: Message) -> str:
    # Prefer real user when available
    user = message.from_user
    if user and user.username:
        return f"@{user.username}"
    if user:
        first = user.first_name or ""
        last = user.last_name or ""
        full = (first + " " + last).strip()
        if full:
            return full
    # Author signature (channels or signed posts)
    if getattr(message, "author_signature", None):
        return message.author_signature
    # Do NOT fallback to chat/sender_chat title; we want the human sender only
    return "unknown"


def build_ydl() -> YoutubeDL:
    ydl_opts = {
        "outtmpl": os.path.join(tempfile.gettempdir(), "%(id)s.%(ext)s"),
        "format": "mp4/best/bestvideo+bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    return YoutubeDL(ydl_opts)


def download_video_to_temp(url: str) -> str:
    with build_ydl() as ydl:
        info = ydl.extract_info(url, download=True)
        # Prefer requested_downloads filepath if present
        requested = info.get("requested_downloads") or []
        if requested and isinstance(requested, list):
            path = requested[0].get("filepath")
            if path and os.path.exists(path):
                return path
        # Fallbacks used by yt-dlp
        for key in ("_filename", "filepath"):
            path = info.get(key)
            if path and os.path.exists(path):
                return path
        raise RuntimeError("Failed to determine the downloaded video path")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    logger.info("/start from %s", message.from_user.id if message.from_user else "unknown")
    await message.answer(
        "Send a TikTok, Instagram Reels, or YouTube Shorts link — I will download and send the video"
    )


def extract_url_from_entities(message: Message) -> str | None:
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    # Prefer explicit text_link URLs
    for ent in entities:
        if getattr(ent, "type", None) == "text_link" and getattr(ent, "url", None):
            return ent.url
    # Fallback: slice URLs from text by 'url' entity ranges
    for ent in entities:
        if getattr(ent, "type", None) == "url" and text:
            try:
                return text[ent.offset : ent.offset + ent.length]
            except Exception:
                continue
    return None


async def _process_message(message: Message) -> None:
    content_text = message.text or message.caption or ""
    chat_type = getattr(message.chat, "type", None)
    url = extract_first_url(content_text) or extract_url_from_entities(message)
    if not url:
        if chat_type == "private":
            logger.info("No URL found in private chat message")
            await message.answer("Is this message a URL?")
        # In groups/channels, ignore silently without logging
        return
    # Log only when we actually have a URL (or in private above)
    logger.info(
        "New message with URL: chat_id=%s chat_type=%s url=%s",
        message.chat.id,
        chat_type,
        url,
    )
    if not is_supported_link(url):
        logger.info("Unsupported URL: %s", url)
        await message.answer("Please send a TikTok, Instagram Reels, or YouTube Shorts link.")
        return

    # Try to delete the original message with the link
    with suppress(Exception):
        await message.delete()

    # show typing/upload indicator while processing
    async with ChatActionSender.upload_video(bot=message.bot, chat_id=message.chat.id):
        try:
            loop = asyncio.get_running_loop()
            video_path = await loop.run_in_executor(None, download_video_to_temp, url)
            logger.info("Downloaded video to: %s", video_path)
        except Exception as e:
            logger.exception("Download failed for URL %s: %s", url, e)
            await message.answer("Failed to download the video. Please try another link.")
            return

    sender_label = get_human_name(message)
    try:
        u = message.from_user
        logger.info(
            "Sender resolved: id=%s username=%s first=%s last=%s -> label=%s",
            getattr(u, "id", None) if u else None,
            getattr(u, "username", None) if u else None,
            getattr(u, "first_name", None) if u else None,
            getattr(u, "last_name", None) if u else None,
            sender_label,
        )
    except Exception:
        pass
    caption = f"Sender: {sender_label}"

    try:
        logger.info("Sending video to chat_id=%s", message.chat.id)
        await message.bot.send_video(
            chat_id=message.chat.id,
            video=FSInputFile(video_path),
            caption=caption,
            supports_streaming=True,
            request_timeout=300,
        )
    except Exception:
        logger.exception("Sending as video failed, trying as document")
        try:
            await message.bot.send_document(
                chat_id=message.chat.id,
                document=FSInputFile(video_path),
                caption=caption,
                request_timeout=300,
            )
        except Exception:
            logger.exception("Sending as document failed as well")
            await message.answer("An error occurred while sending the video")
    finally:
        with suppress(Exception):
            if os.path.exists(video_path):
                os.remove(video_path)


@router.message()
async def handle_message(message: Message) -> None:
    await _process_message(message)


@router.edited_message()
async def handle_edited_message(message: Message) -> None:
    await _process_message(message)


@router.channel_post()
async def handle_channel_post(message: Message) -> None:
    await _process_message(message)


@router.edited_channel_post()
async def handle_edited_channel_post(message: Message) -> None:
    await _process_message(message)


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Add it to .env or environment variables.")
    # Increase HTTP timeouts for large uploads
    session = AiohttpSession(timeout=300)
    bot = Bot(token=token, session=session)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())



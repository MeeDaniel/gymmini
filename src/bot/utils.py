import os
import io
import re
import json
import logging
import aiohttp
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from src.core.config import settings

telegraph_token = settings.telegraph_token

async def create_telegraph_page(title: str, text: str) -> str | None:
    url = "https://api.telegra.ph/createPage"
    content = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        lines = para.split("\n")
        children = []
        for i, line in enumerate(lines):
            children.append(line)
            if i < len(lines) - 1:
                children.append({"tag": "br"})
        content.append({"tag": "p", "children": children})
    if not content:
        content = [{"tag": "p", "children": ["(Описание отсутствует)"]}]
        
    payload = {
        "access_token": telegraph_token,
        "title": (title[:250] if title else "Описание"),
        "content": json.dumps(content, ensure_ascii=False),
        "return_content": "false"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    return data["result"]["url"]
    except Exception as e:
        logging.error(f"Failed to create Telegraph page: {e}")
    return None

async def format_description_preview(description: str | None, max_len: int = 300, title: str = "Описание") -> str:
    if not description:
        return "Нет"
    if len(description) <= max_len:
        return description
    
    url = await create_telegraph_page(title, description)
    preview = description[:max_len] + "..."
    if url:
        return f"{preview}\n\n📄 Полное описание: {url}"
    return f"{preview}\n\n... (слишком длинное описание)"

async def cleanup_previous_file(target: CallbackQuery | Message, state: FSMContext | None = None):
    # No-op since we no longer send or manage auxiliary .md files above cards.
    if state:
        await state.update_data(last_file_msg_id=None)

async def extract_description_text(message: Message) -> tuple[str | None, str | None]:
    if message.text:
        return message.text, None
    if message.document:
        doc = message.document
        if doc.file_size and doc.file_size > 1024 * 1024:
            return None, "Файл слишком большой. Максимальный размер: 1 МБ."
        
        name = (doc.file_name or "").lower()
        if "." in name and not (name.endswith(".txt") or name.endswith(".md")):
            return None, "Пожалуйста, отправьте текстовый файл формата .txt или .md (либо обычный текст в чате)."
        
        file_path = await message.bot.get_file(doc.file_id)
        buffer = io.BytesIO()
        await message.bot.download_file(file_path.file_path, buffer)
        content_bytes = buffer.getvalue()
        
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                return content_bytes.decode(enc), None
            except UnicodeDecodeError:
                continue
        return None, "Не удалось распознать кодировку текстового файла."
    
    return None, "Пожалуйста, отправьте описание текстом или прикрепите файл .txt / .md."

from aiogram.exceptions import TelegramBadRequest

async def edit_message_text_or_caption(message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None):
    try:
        if message.photo:
            await message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await message.edit_text(text=text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower(): return
        try: await message.delete()
        except: pass
        await message.answer(text, reply_markup=reply_markup)
    except Exception:
        try: await message.delete()
        except: pass
        await message.answer(text, reply_markup=reply_markup)

async def send_card_with_optional_file(
    target: CallbackQuery | Message,
    title: str,
    description: str | None,
    card_text: str,
    reply_markup: InlineKeyboardMarkup,
    image_path: str | None = None,
    state: FSMContext | None = None
):
    msg_target = target.message if isinstance(target, CallbackQuery) else target
    
    # Try editing in place if it's a callback query
    if isinstance(target, CallbackQuery):
        try:
            if image_path and os.path.exists(image_path):
                media = InputMediaPhoto(media=FSInputFile(image_path), caption=card_text)
                await msg_target.edit_media(media=media, reply_markup=reply_markup)
                return
            else:
                if not msg_target.photo:
                    await msg_target.edit_text(card_text, reply_markup=reply_markup)
                    return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower(): return
        except Exception:
            pass
            
    # Fallback to delete existing card and answer fresh
    try:
        await msg_target.delete()
    except Exception:
        pass

    if image_path and os.path.exists(image_path):
        await msg_target.answer_photo(
            FSInputFile(image_path),
            caption=card_text,
            reply_markup=reply_markup
        )
    else:
        await msg_target.answer(
            text=card_text,
            reply_markup=reply_markup
        )


import os
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8626456969:AAFFHffm16ikzert9G0qIIKaIlvCmnEK4Ts"

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def start(update, context):
    await update.message.reply_text("🎬 Отправьте ссылку на Rutube!")

async def handle_url(update, context):
    url = update.message.text
    if "rutube.ru" not in url:
        await update.message.reply_text("❌ Нужна ссылка с rutube.ru")
        return
    
    context.user_data['url'] = url
    msg = await update.message.reply_text("🔍 Получаю информацию...")
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Видео')[:40]
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 Видео", callback_data="video")],
                [InlineKeyboardButton("🎵 MP3", callback_data="audio")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ])
            await msg.edit_text(f"📹 {title}\n\nВыберите:", reply_markup=kb)
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")

async def callback(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Отменено")
        return
    
    url = context.user_data.get('url')
    if not url:
        await query.edit_message_text("❌ Ошибка, отправьте ссылку заново")
        return
    
    await query.edit_message_text("⏳ Скачиваю... Подождите...")
    
    try:
        if query.data == "video":
            opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                with open(filename, 'rb') as f:
                    await query.message.reply_video(f, caption=f"✅ {info.get('title', 'Видео')[:50]}")
                os.remove(filename)
        else:
            opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"downloads/{info['title']}.mp3"
                with open(filename, 'rb') as f:
                    await query.message.reply_audio(f, title=info.get('title', 'Аудио')[:50])
                os.remove(filename)
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)[:150]}")

def main():
    print("🤖 Бот запущен!")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(callback))
    print("✅ Готов!")
    app.run_polling()

if __name__ == "__main__":
    main()

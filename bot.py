import os
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp
import logging

# Включаем логирование для отслеживания ошибок
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: переменная BOT_TOKEN не установлена!")
    exit(1)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def start(update: Update, context):
    await update.message.reply_text(
        "🎬 *Rutube Downloader Bot*\n\n"
        "Я умею скачивать видео с Rutube!\n\n"
        "📌 *Как пользоваться:*\n"
        "1. Отправьте ссылку на видео Rutube\n"
        "2. Выберите формат (видео или аудио)\n"
        "3. Получите готовый файл!\n\n"
        "⚡ Поддерживается: MP4 видео и MP3 аудио\n\n"
        "Просто отправьте ссылку!",
        parse_mode='Markdown'
    )

async def handle_url(update: Update, context):
    url = update.message.text.strip()
    
    if not re.search(r'rutube\.ru', url):
        await update.message.reply_text("❌ Пожалуйста, отправьте ссылку с Rutube (rutube.ru)")
        return
    
    context.user_data['video_url'] = url
    status_msg = await update.message.reply_text("🔍 Получаю информацию...")
    
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Видео')[:50]
            
            keyboard = [
                [InlineKeyboardButton("📹 Видео", callback_data="video")],
                [InlineKeyboardButton("🎵 MP3 аудио", callback_data="audio")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            
            await status_msg.edit_text(
                f"📹 *{title}*\n\nВыберите формат:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Отменено")
        return
    
    video_url = context.user_data.get('video_url')
    if not video_url:
        await query.edit_message_text("❌ Ошибка: отправьте ссылку заново")
        return
    
    await query.edit_message_text("⏳ Скачиваю... Подождите...")
    
    try:
        if query.data == "video":
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                
                with open(filename, 'rb') as f:
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=f,
                        caption=f"✅ {info.get('title', 'Видео')[:50]}"
                    )
                os.remove(filename)
                
        elif query.data == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
                'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = str(DOWNLOAD_DIR / f"{info['title']}.mp3")
                
                with open(filename, 'rb') as f:
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=f,
                        title=info.get('title', 'Аудио')[:50]
                    )
                os.remove(filename)
        
        context.user_data.clear()
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)[:150]}")

def main():
    print("🤖 Rutube Downloader Bot запущен!")
    print(f"BOT_TOKEN установлен: {'Да' if BOT_TOKEN else 'Нет'}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()

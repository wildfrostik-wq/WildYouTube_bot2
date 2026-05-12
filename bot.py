import os
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8626456969:AAFFHffm16ikzert9G0qIIKaIlvCmnEK4Ts")

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def start(update: Update, context):
    await update.message.reply_text("🎬 Отправьте ссылку на YouTube или Rutube!")

async def handle_url(update: Update, context):
    url = update.message.text.strip()
    
    if not re.search(r'(youtube|youtu|rutube)', url):
        await update.message.reply_text("❌ Отправьте ссылку на YouTube или Rutube")
        return
    
    context.user_data['video_url'] = url
    status_msg = await update.message.reply_text("🔍 Получаю информацию...")
    
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Видео')[:50]
            
            keyboard = [
                [InlineKeyboardButton("📹 Видео 480p", callback_data="video")],
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
        await query.edit_message_text("❌ Отправьте ссылку заново")
        return
    
    await query.edit_message_text("⏳ Скачиваю... Подождите...")
    
    try:
        if query.data == "video":
            ydl_opts = {
                'format': 'best[height<=480][ext=mp4]',
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
    print("🤖 Бот запущен на Render!")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_polling()

if __name__ == '__main__':
    main()

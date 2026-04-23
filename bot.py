import os
import base64
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์คอนเทนต์และการตลาดดิจิทัล Facebook Ads

เมื่อได้รับข้อความหรือภาพ thumbnail จากวิดีโอ ให้วิเคราะห์และตอบกลับดังนี้:

📊 *สรุปเนื้อหา*
[สรุป 2-3 ประโยค]

🗂 *หมวดหมู่:* [หมวดหมู่]
👤 *กลุ่มเป้าหมาย:* [กลุ่มเป้าหมาย]

🔥 *จุดเด่น*
• [จุดเด่น 1]
• [จุดเด่น 2]
• [จุดเด่น 3]

✍️ *พาดหัวโฆษณา Facebook*
⚡ ดึงดูด: [พาดหัว]
🎯 ประโยชน์: [พาดหัว]
🔥 เร่งด่วน: [พาดหัว]
💡 คำถาม: [พาดหัว]
👥 Social Proof: [พาดหัว]

📝 *Primary Text*
[ข้อความหลักโฆษณา 2-3 ประโยค]

🎯 *CTA:* [Call-to-Action]

💡 *เคล็ดลับยิงแอด*
• [เคล็ดลับ 1]
• [เคล็ดลับ 2]
• [เคล็ดลับ 3]"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 สวัสดีครับ! ผมคือบอทวิเคราะห์คอนเทนต์\n\n"
        "📌 วิธีใช้งาน:\n"
        "• ส่งข้อความที่ต้องการวิเคราะห์\n"
        "• ส่งวิดีโอมาได้เลย 🎥 (วิเคราะห์จาก thumbnail)\n"
        "• ส่งรูปภาพมาได้เลย 🖼\n"
        "• /analyze [ข้อความ]\n\n"
        "🚀 พร้อมสร้างพาดหัวแอด Facebook ให้ทันที!"
    )


async def analyze_text(text: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"วิเคราะห์คอนเทนต์นี้:\n\n{text}"}],
    )
    return message.content[0].text


async def analyze_image(image_data: bytes, caption: str = "") -> str:
    image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_b64,
            },
        },
        {
            "type": "text",
            "text": f"วิเคราะห์คอนเทนต์จากภาพนี้{f' และข้อความ: {caption}' if caption else ''}",
        },
    ]
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    if CHAT_ID and chat_id != CHAT_ID and update.effective_chat.type != "private":
        return

    caption = update.message.caption or ""

    # Handle video — ดึง thumbnail มาวิเคราะห์
    if update.message.video:
        status_msg = await update.message.reply_text("🎥 กำลังวิเคราะห์วิดีโอ...")
        try:
            video = update.message.video
            # ดึง thumbnail
            if video.thumbnail:
                thumb_file = await context.bot.get_file(video.thumbnail.file_id)
                thumb_data = bytes(await thumb_file.download_as_bytearray())
                result = await analyze_image(thumb_data, caption)
            elif caption:
                result = await analyze_text(caption)
            else:
                result = "❌ ไม่สามารถดึง thumbnail ได้ กรุณาส่งข้อความ caption ด้วยครับ"
            await status_msg.edit_text(result, parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return

    # Handle photo
    if update.message.photo:
        status_msg = await update.message.reply_text("🖼 กำลังวิเคราะห์รูปภาพ...")
        try:
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)
            photo_data = bytes(await photo_file.download_as_bytearray())
            result = await analyze_image(photo_data, caption)
            await status_msg.edit_text(result, parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        return

    # Handle text
    if update.message.text and not update.message.text.startswith("/"):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            result = await analyze_text(update.message.text)
            await update.message.reply_text(result, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❗ เช่น: /analyze ข้อความที่ต้องการวิเคราะห์")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        result = await analyze_text(" ".join(context.args))
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    print("🤖 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

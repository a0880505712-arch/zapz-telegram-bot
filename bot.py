import os
import anthropic
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์คอนเทนต์และการตลาดดิจิทัล Facebook Ads

เมื่อได้รับข้อความหรือ transcript จากวิดีโอ ให้วิเคราะห์และตอบกลับดังนี้:

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
        "• ส่งวิดีโอจากกลุ่มมาได้เลย 🎥\n"
        "• /analyze [ข้อความ] - วิเคราะห์ข้อความ\n\n"
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


async def transcribe_audio(file_path: str) -> str:
    import openai
    openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    with open(file_path, "rb") as f:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="th"
        )
    return transcript.text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    chat_id = str(update.effective_chat.id)
    if CHAT_ID and chat_id != CHAT_ID and update.effective_chat.type != "private":
        return

    # Handle video
    if update.message.video or update.message.video_note:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        status_msg = await update.message.reply_text("🎥 กำลังประมวลผลวิดีโอ รอสักครู่...")

        try:
            video = update.message.video or update.message.video_note
            file = await context.bot.get_file(video.file_id)

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                await file.download_to_drive(tmp.name)
                tmp_path = tmp.name

            await status_msg.edit_text("🎙 กำลังถอดเสียง...")
            transcript = await transcribe_audio(tmp_path)
            os.unlink(tmp_path)

            if not transcript.strip():
                await status_msg.edit_text("❌ ไม่พบเสียงพูดในวิดีโอครับ")
                return

            await status_msg.edit_text("🤖 กำลังวิเคราะห์...")
            result = await analyze_text(f"[Transcript จากวิดีโอ]\n{transcript}")
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
    application.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_message))
    print("🤖 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

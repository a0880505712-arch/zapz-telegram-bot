import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์คอนเทนต์และการตลาดดิจิทัล Facebook Ads

เมื่อได้รับข้อความ ให้วิเคราะห์และตอบกลับดังนี้:

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
        "• ส่งข้อความที่ต้องการวิเคราะห์มาได้เลย\n"
        "• /analyze [ข้อความ] - วิเคราะห์ข้อความ\n\n"
        "🚀 พร้อมสร้างพาดหัวแอด Facebook ให้ทันที!"
    )


async def analyze_text(text: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"วิเคราะห์คอนเทนต์นี้:\n\n{text}"}],
    )
    return message.content[0].text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    if CHAT_ID and chat_id != CHAT_ID and update.effective_chat.type != "private":
        return

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
    print("🤖 Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

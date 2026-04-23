import os
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CHAT_ID = os.environ.get("CHAT_ID", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์คอนเทนต์และการตลาดดิจิทัล Facebook Ads

เมื่อได้รับข้อความจากกลุ่มเทเลแกรม ให้วิเคราะห์และตอบกลับในรูปแบบที่อ่านง่ายในเทเลแกรม:

📊 *สรุปเนื้อหา*
[สรุป 2-3 ประโยค]

🗂 *หมวดหมู่:* [หมวดหมู่]
👤 *กลุ่มเป้าหมาย:* [กลุ่มเป้าหมาย]
🎭 *โทน:* [โทน]

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
[ข้อความหลักโฆษณา]

🎯 *CTA:* [Call-to-Action]

💡 *เคล็ดลับยิงแอด*
• [เคล็ดลับ 1]
• [เคล็ดลับ 2]
• [เคล็ดลับ 3]"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 สวัสดีครับ! ผมคือบอทวิเคราะห์คอนเทนต์\n\n"
        "📌 วิธีใช้งาน:\n"
        "• ส่งข้อความที่ต้องการวิเคราะห์มาได้เลย\n"
        "• หรือใช้คำสั่ง /analyze [ข้อความ]\n\n"
        "🚀 พร้อมวิเคราะห์และสร้างพาดหัวแอด Facebook ให้ทันที!"
    )


async def analyze_text(text: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"วิเคราะห์คอนเทนต์นี้:\n\n{text}"}],
    )
    return message.content[0].text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    if CHAT_ID and chat_id != CHAT_ID and update.effective_chat.type != "private":
        return

    text = update.message.text
    if text.startswith("/"):
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        result = await analyze_text(text)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❗ กรุณาระบุข้อความ เช่น:\n/analyze ข้อความที่ต้องการวิเคราะห์"
        )
        return

    text = " ".join(context.args)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        result = await analyze_text(text)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ เกิดข้อผิดพลาด: {str(e)}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()

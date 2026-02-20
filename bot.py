import os
import nest_asyncio

from smolagents import ToolCallingAgent, WebSearchTool, InferenceClientModel
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

# Allow async polling in hosted environments
nest_asyncio.apply()

# Read tokens from environment
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

# Model ID you are happy with
# MODEL_ID = "Qwen/Qwen3-Coder-Next"
MODEL_ID="moonshotai/Kimi-K2-Instruct"

# Build model + agent

model = InferenceClientModel(model_id=MODEL_ID, provider="novita")

agent = ToolCallingAgent(model=model,
                         tools=[WebSearchTool()])
                         # max_steps=2) # maybe i'll just let it work for as long as it needs
#
# Memory store per user
#
user_memory = {}

#
# Handlers
#

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_memory[user_id] = []
    await update.message.reply_text("🧹 Memory cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(f"User: {user_text}")

    # Build prompt with memory
    prompt = "\n".join(user_memory[user_id]) + "\nAssistant:"

    try:
        # Run the smolagents agent — it will call the search tool if needed
        result = agent.run(prompt)

        # Agent returns a string
        reply = result if isinstance(result, str) else str(result)

        # Save assistant output
        user_memory[user_id].append(f"Assistant: {reply}")

    except Exception as e:
        reply = f"⚠️ Agent error: {e}"

    await update.message.reply_text(reply)

#
# Start the bot
#

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("reset", reset_memory))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("📡 Bot starting…")
app.run_polling()

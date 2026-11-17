import os
import json
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"
TOKEN = "YOUR_BOT_TOKEN_HERE"
ALLOWED_USER_ID = 123456789 # replace with your Telegram user ID

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error: {e}"

def web_search(query):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found."
            return "\n\n".join([f"{r['title']}\n{r['body']}" for r in results])
    except Exception as e:
        return f"Search error: {e}"

tools = {
    "list_files": list_files,
    "web_search": web_search,
}

def ask_astrum(user_message: str) -> str:
    messages = [{
        "role": "system",
        "content": """You are Astrum, a helpful local agent.
You have tools, but only use them when you need external or real-time information you don't already know.
For questions about yourself, your name, or general knowledge, just answer directly.
When you do need a tool, reply with ONLY JSON like:
{"tool": "web_search", "args": {"query": "your search"}}
or
{"tool": "list_files", "args": {"path": "."}}
After getting a tool result, give a normal final answer. Do not call the tool again."""
    }, {"role": "user", "content": user_message}]

    # First call
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages, "stream": False})
    reply = resp.json()["message"]["content"]

    # Tool handling (same logic as before)
    try:
        if "{" in reply and "}" in reply:
            start = reply.find("{")
            end = reply.rfind("}") + 1
            call = json.loads(reply[start:end])
            tool_name = call.get("tool")
            args = call.get("args", {})
            if tool_name in tools:
                result = tools[tool_name](**args)
                messages.append({"role": "user", "content": f"Tool result: {result}"})
                final_resp = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages, "stream": False})
                return final_resp.json()["message"]["content"]
    except:
        pass

    return reply

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return  # ignore everyone else
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    answer = ask_astrum(user_text)
    await update.message.reply_text(answer)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Astrum Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()






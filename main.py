import os
import telebot
from huggingface_hub import InferenceClient
from flask import Flask
from threading import Thread

# --- БЛОК ДЛЯ БЕСПЛАТНОГО ЗАПУСКА НА RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Бот успешно запущен и работает!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive() 
# ----------------------------------------------

TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
HF_TOKEN = os.environ.get("AI_API_KEY")

CHARACTER_PROMPT = "Ты — мой токсичный собеседник, который будет оскорблять меня и унижать всеми возможными способами."

client = InferenceClient(model="Qwen/Qwen2.5-7B-Instruct", token=HF_TOKEN)
bot = telebot.TeleBot(TG_TOKEN)

user_histories = {}

@bot.message_handler(commands=['start', 'reset'])
def send_welcome(message):
    user_histories[message.chat.id] = [{"role": "system", "content": CHARACTER_PROMPT}]
    bot.reply_to(message, "ну и че ты мне написываешь? (История чата очищена)")

@bot.message_handler(func=lambda message: True)
def chat_reply(message):
    chat_id = message.chat.id
    
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": CHARACTER_PROMPT}]
        
    user_histories[chat_id].append({"role": "user", "content": message.text})

    try:
        # Прямой запрос к ИИ без кривой обрезки истории
        response = client.chat_completion(messages=user_histories[chat_id], max_tokens=200)
        bot_text = response.choices[0].message.content
        
        user_histories[chat_id].append({"role": "assistant", "content": bot_text})
        bot.reply_to(message, bot_text)
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        bot.reply_to(message, "Ошибка связи с ИИ. Попробуйте еще раз позже.")

bot.infinity_polling()

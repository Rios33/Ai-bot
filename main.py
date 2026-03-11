import requests
import socket
import re
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения
load_dotenv()

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

print(f"Бот запускается с токеном: {TOKEN[:20]}...")


# Функция для AI
async def ask_gpt(question):
    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"}
    data = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": question}]}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            return f"Ошибка API: {r.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"


# Функция для получения информации по IP
async def get_ip_info(ip_address=None):
    try:
        if ip_address:
            url = f"http://ip-api.com/json/{ip_address}?lang=ru"
        else:
            url = "http://ip-api.com/json/?lang=ru"

        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('status') == 'success':
            result = f"Информация по IP:\n"
            result += f"IP: {data.get('query', 'Неизвестно')}\n"
            result += f"Город: {data.get('city', 'Неизвестно')}\n"
            result += f"Регион: {data.get('regionName', 'Неизвестно')}\n"
            result += f"Страна: {data.get('country', 'Неизвестно')}\n"
            result += f"Провайдер: {data.get('isp', 'Неизвестно')}\n"
            result += f"Часовой пояс: {data.get('timezone', 'Неизвестно')}\n"
            return result
        else:
            return f"Не удалось определить местоположение"
    except Exception as e:
        return f"Ошибка: {e}"


# Получение IP домена
def get_domain_ip(domain):
    try:
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.split('/')[0].split('?')[0]
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        return None


# Извлечение IP из текста
def extract_ip_from_text(text):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    match = re.search(ip_pattern, text)
    return match.group(0) if match else None


# Извлечение домена из текста
def extract_domain_from_text(text):
    domain_pattern = r'\b[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]?(?:\.[a-zA-Z]{2,})+\b'
    match = re.search(domain_pattern, text)
    return match.group(0) if match else None


# Проверка, спрашивает ли пользователь про IP
def is_ip_query(text):
    text_lower = text.lower()
    ip_keywords = ['ip', 'айпи', 'мой ip', 'где находится', 'местоположение', 'узнай ip', 'какой ip', 'покажи ip']
    return any(keyword in text_lower for keyword in ip_keywords)


# Основной обработчик
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action(action="typing")

    print(f"Получено сообщение: {user_text}")  # Отладка

    if is_ip_query(user_text):
        ip = extract_ip_from_text(user_text)
        if ip:
            result = await get_ip_info(ip)
            await update.message.reply_text(result)
            return

        domain = extract_domain_from_text(user_text)
        if domain:
            domain_ip = get_domain_ip(domain)
            if domain_ip:
                result = await get_ip_info(domain_ip)
                await update.message.reply_text(f"{domain}\n IP: {domain_ip}\n\n{result}")
            else:
                await update.message.reply_text(f"Не удалось определить IP для {domain}")
            return

        # Если просто спросили про IP без указания
        result = await get_ip_info()
        await update.message.reply_text(result)
        return

    # Обычный вопрос к GPT
    answer = await ask_gpt(user_text)
    await update.message.reply_text(answer)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с GPT и определением IP!\n\n"
        "Пиши любые вопросы, я отвечу.\n"
        "Если спросишь про IP, покажу информацию.\n\n"
        "Примеры:\n"
        "- какой у меня IP\n"
        "- где находится 8.8.8.8\n"
        "- ip google.com\n"
        "- узнай yandex.ru"
    )


def main():
    print("Бот запущен...")

    # Проверка наличия токена
    if not TOKEN:
        print("ОШИБКА: Токен бота не найден!")
        return

    # Создание приложения
    app = Application.builder().token(TOKEN).build()

    # Добавление обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    print("Бот готов к работе!")
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")
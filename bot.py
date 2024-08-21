import os
import re
import requests
from bs4 import BeautifulSoup
from telebot import TeleBot

# Función para limpiar el nombre de la página
def clean_filename(name):
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return name

# Obtener el token del bot de Telegram desde una variable de entorno
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("El token del bot de Telegram no está configurado en las variables de entorno.")

bot = TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.reply_to(message, "Funcionando...")

@bot.message_handler(commands=['info'])
def send_info(message):
    code = message.text.split()[1] if len(message.text.split()) > 1 else None
    if not code:
        bot.reply_to(message, "Por favor, proporciona un código.")
        return

    url = f"https://es.3hentai.net/d/{code}/"
    response = requests.get(url)
    if response.status_code != 200:
        bot.reply_to(message, "No se pudo acceder a la página.")
        return

    page_title = re.search(r'<title>(.*?)</title>', response.text).group(1)
    clean_title = clean_filename(page_title) + f"_{code}"

    # Analizar el contenido HTML de la página para encontrar la imagen
    soup = BeautifulSoup(response.content, 'html.parser')
    image_tag = soup.find('img', {'src': re.compile(r'cover\.jpg')})
    if not image_tag:
        bot.reply_to(message, "No se encontró la imagen cover.jpg en la página.")
        return

    image_url = image_tag['src']
    if not image_url.startswith('http'):
        image_url = f"{url}{image_url}"

    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        bot.reply_to(message, "No se pudo descargar la imagen.")
        return

    image_path = f"/tmp/{clean_title}.jpg"
    with open(image_path, 'wb') as f:
        f.write(image_response.content)

    with open(image_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=clean_title)

    os.remove(image_path)

if __name__ == '__main__':
    bot.polling()

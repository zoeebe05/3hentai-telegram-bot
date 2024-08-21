import os
import re
import requests
from telebot import TeleBot

# Función para limpiar el nombre de la página
def clean_filename(name):
    # Eliminar caracteres no permitidos y letras no inglesas
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    return name

# Obtener el token del bot de Telegram desde una variable de entorno
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("El token del bot de Telegram no está configurado en las variables de entorno.")

bot = TeleBot(TOKEN)

@bot.message_handler(commands=['info'])
def send_info(message):
    # Obtener el código del comando
    code = message.text.split()[1] if len(message.text.split()) > 1 else None
    if not code:
        bot.reply_to(message, "Por favor, proporciona un código.")
        return

    # Construir la URL
    url = f"https://www/d/{code}/"

    # Obtener el contenido de la página
    response = requests.get(url)
    if response.status_code != 200:
        bot.reply_to(message, "No se pudo acceder a la página.")
        return

    # Extraer el nombre de la página (suponiendo que está en el título)
    page_title = re.search(r'<title>(.*?)</title>', response.text).group(1)
    clean_title = clean_filename(page_title) + f"_{code}"

    # Descargar la imagen cover.jpg
    image_url = f"{url}cover.jpg"
    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        bot.reply_to(message, "No se pudo descargar la imagen.")
        return

    # Guardar la imagen temporalmente
    image_path = f"/tmp/{clean_title}.jpg"
    with open(image_path, 'wb') as f:
        f.write(image_response.content)

    # Enviar la imagen y el texto al usuario
    with open(image_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=clean_title)

    # Eliminar la imagen temporal
    os.remove(image_path)

if __name__ == '__main__':
    bot.polling()

import os
import re
import requests
from bs4 import BeautifulSoup
from telebot import TeleBot
import zipfile
from PIL import Image
from io import BytesIO

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

@bot.message_handler(commands=['ima'])
def handle_ima_command(message):
    code = message.text.split()[1]  # Suponiendo que el código es el segundo argumento
    url = f"https://es.3hentai.net/d/{code}"
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        image_links = [img['src'].replace('t.jpg', '.jpg') for img in soup.find_all('img') if img['src'].endswith('t.jpg')]
        
        for link in image_links:
            image_response = requests.get(link)
            if image_response.status_code == 200:
                image = BytesIO(image_response.content)
                bot.send_photo(message.chat.id, image)
            else:
                bot.reply_to(message, f"No se pudo descargar la imagen: {link}")
    else:
        bot.reply_to(message, "No se pudo acceder al enlace proporcionado.")


@bot.message_handler(commands=['cbz'])
def handle_cbz_command(message):
    code = message.text.split()[1]  # Suponiendo que el código es el segundo argumento
    url = f"https://es.3hentai.net/d/{code}"
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        image_links = [img['src'].replace('t.jpg', '.jpg') for img in soup.find_all('img') if img['src'].endswith('t.jpg')]
        
        images = []
        for link in image_links:
            image_response = requests.get(link)
            if image_response.status_code == 200:
                image = Image.open(BytesIO(image_response.content))
                images.append(image)
            else:
                bot.reply_to(message, f"No se pudo descargar la imagen: {link}")
        
        if images:
            cbz_file = create_cbz(images, code)
            with open(cbz_file, 'rb') as file:
                bot.send_document(message.chat.id, file)
            os.remove(cbz_file)
        else:
            bot.reply_to(message, "No se encontraron imágenes para crear el archivo CBZ.")
    else:
        bot.reply_to(message, "No se pudo acceder al enlace proporcionado.")

def create_cbz(images, code):
    cbz_filename = f"{code}.cbz"
    with zipfile.ZipFile(cbz_filename, 'w') as cbz:
        for i, image in enumerate(images):
            image_filename = f"image_{i}.jpg"
            image.save(image_filename)
            cbz.write(image_filename)
            os.remove(image_filename)
    return cbz_filename

if __name__ == '__main__':
    bot.polling()
    

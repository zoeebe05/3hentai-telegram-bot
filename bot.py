import os
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from PIL import Image
import shutil
import zipfile

# Configura tu token de bot de Telegram
TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('¡Hola! Usa /d <Código> para comenzar.')

def download_images(update: Update, context: CallbackContext) -> None:
    code = context.args[0]
    user_id = update.message.from_user.id
    chat_id = os.getenv('teleuser')
bot.send_message(chat_id=chat_id, text='Estoy listo')
    
    url = f'https:/es.3hentai.net/d/{code}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Captura todos los links de imágenes
    image_links = [img['src'] for img in soup.find_all('img') if img['src'].endswith('.jpg')]
    
    # Edita los links de las imágenes
    image_links = [link.replace('t.jpg', '.jpg') for link in image_links]
    
    # Captura el nombre de la página
    page_name = soup.title.string.strip()
    
    # Elimina caracteres no válidos para nombres de archivos
    page_name = re.sub(r'[\\/*?:"<>|]', "", page_name)
    
    # Nombre de la carpeta
    folder_name = f"{page_name} ({code})"
    
    # Si el nombre de la carpeta es muy largo, reducir caracteres
    if len(folder_name) > 255:
        folder_name = folder_name[:255]
    
    # Crear la carpeta
    os.makedirs(folder_name, exist_ok=True)
    
    # Descargar las imágenes
    for i, link in enumerate(image_links):
        img_data = requests.get(link).content
        with open(os.path.join(folder_name, f'image_{i+1}.jpg'), 'wb') as handler:
            handler.write(img_data)
    
    # Comprimir la carpeta en un archivo CBZ
    cbz_filename = f"{folder_name}.cbz"
    with zipfile.ZipFile(cbz_filename, 'w') as cbz:
        for root, _, files in os.walk(folder_name):
            for file in files:
                cbz.write(os.path.join(root, file), arcname=file)
    
    # Enviar el archivo al usuario que lo solicitó
    bot.send_document(chat_id=user_id, document=open(cbz_filename, 'rb'))
    
    # Limpiar archivos temporales
    shutil.rmtree(folder_name)
    os.remove(cbz_filename)

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("d", download_images))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

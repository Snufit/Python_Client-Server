# -*- coding: utf-8 -*-
import os
import time
import logging
import http.server
import socketserver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [VISUALIZATION] - %(message)s',
    handlers=[
        logging.FileHandler('visualization.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PORT = 8000
DIRECTORY = r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server"

def wait_for_file(filename, max_wait=30):
    wait_time = 0
    while not os.path.exists(filename) and wait_time < max_wait:
        logger.debug(f"Ожидание {filename}, попытка {wait_time + 1}/{max_wait}")
        time.sleep(1)
        wait_time += 1
    if not os.path.exists(filename):
        logger.warning(f"Файл {filename} не найден после {max_wait} секунд")
        return False
    return True

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    logger.info(f"Запуск визуализации, текущая директория: {os.getcwd()}")
    logger.info(f"Доступные файлы в директории {DIRECTORY}: {os.listdir(DIRECTORY)}")

    if not wait_for_file("server_resources.json"):
        exit(1)

    if "index.html" in os.listdir(DIRECTORY):
        logger.info("Файл index.html найден в директории")
    else:
        logger.error("Файл index.html не найден")
        exit(1)

    with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        logger.info(f"Веб-сервер запущен на http://localhost:{PORT}, текущая директория: {os.getcwd()}")
        import webbrowser
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        logger.info("Браузер открыт для визуализации")
        httpd.serve_forever()
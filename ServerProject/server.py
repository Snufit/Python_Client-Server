# -*- coding: utf-8 -*-
import c104
import time
import random
import logging
import psutil
import threading
import json
import os
import sys

os.chdir(r'C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server')
sys.path.append(r'C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server')
from logging_config import setup_resource_logger

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [SERVER] - %(message)s',
    handlers=[
        logging.FileHandler('server.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

resource_logger = setup_resource_logger()

def save_resource_data(cpu_percent, memory_percent, timestamp, filename=r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\server_resources.json"):
    logger.debug(f"Вход в save_resource_data, filename={filename}, current dir={os.getcwd()}")
    data = {"timestamp": timestamp, "cpu_percent": cpu_percent, "memory_percent": memory_percent}
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not os.access(os.path.dirname(filename), os.W_OK):
            logger.error(f"Нет прав на запись в {os.path.dirname(filename)}")
            raise PermissionError(f"Нет прав на запись в {os.path.dirname(filename)}")
        
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.debug(f"Файл {filename} прочитан, данных: {len(existing_data)}")
            except json.JSONDecodeError:
                logger.warning(f"Файл {filename} повреждён, создаём новый")
                existing_data = []
        existing_data = [d for d in existing_data if d['timestamp'] != timestamp]
        existing_data.append(data)
        
        # Попытка записи с обработкой блокировки
        max_attempts = 3
        for attempt in range(max_attempts):
            temp_file = filename + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=4)
                os.replace(temp_file, filename)
                logger.info(f"Сохранены данные ресурсов в {filename}: {data}")
                resource_logger.info(f"Сервер - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s")
                break
            except PermissionError:
                logger.warning(f"Попытка {attempt + 1}/{max_attempts} записи в {filename} заблокирована")
                if attempt < max_attempts - 1:
                    time.sleep(1)  # Ждём перед следующей попыткой
                else:
                    logger.error(f"Не удалось сохранить данные в {filename} после {max_attempts} попыток")
                    raise
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов в {filename}: {str(e)}", exc_info=True)
        raise

def monitor_resources(stop_event, prefix="СЕРВЕР"):
    global start_time
    logger.debug(f"Запуск monitor_resources для {prefix}")
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        timestamp = int(time.time() - start_time)
        save_resource_data(cpu_percent, memory_percent, timestamp)
        logger.info(f"Начальное использование ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%, Время={timestamp}s")
    except Exception as e:
        logger.error(f"Ошибка начальной записи: {str(e)}", exc_info=True)
        return
    
    while not stop_event.is_set():
        try:
            logger.debug(f"Сервер продолжает работу...")
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            timestamp = int(time.time() - start_time)
            save_resource_data(cpu_percent, memory_percent, timestamp)
            logger.info(f"Использование ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%, Время={timestamp}s")
            if cpu_percent > 80 or memory_percent > 80:
                logger.warning(f"Высокая загрузка ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
        except Exception as e:
            logger.error(f"Ошибка в monitor_resources: {str(e)}", exc_info=True)
        time.sleep(1)  # Уменьшен интервал до 1 секунды для более частого обновления

def main():
    global start_time
    server_json = r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\server_resources.json"
    start_time_json = r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\start_time.json"
    if os.path.exists(server_json):
        try:
            os.remove(server_json)
            logger.info(f"Удалён старый файл {server_json}")
        except Exception as e:
            logger.error(f"Ошибка удаления {server_json}: {str(e)}", exc_info=True)
    if os.path.exists(start_time_json):
        try:
            os.remove(start_time_json)
            logger.info(f"Удалён старый файл {start_time_json}")
        except Exception as e:
            logger.error(f"Ошибка удаления {start_time_json}: {str(e)}", exc_info=True)
    
    start_time = time.time()
    try:
        with open(start_time_json, 'w', encoding='utf-8') as f:
            json.dump({"start_time": start_time}, f)
        logger.info(f"start_time сохранён в {start_time_json}: {start_time}")
    except Exception as e:
        logger.error(f"Ошибка записи start_time.json: {str(e)}", exc_info=True)
        start_time = time.time()
    
    logger.info(f"Текущая рабочая директория: {os.getcwd()}")
    logger.debug("Скрипт сервера запущен")
    
    logger.debug("Перед созданием сервера")
    server = c104.Server(port=2404)  # Указываем порт при инициализации
    logger.debug("Сервер создан")
    station = server.add_station(common_address=1)
    logger.info(f"Станция создана с common_address={station.common_address}")
    
    points = []
    for ioa in range(0, 10):
        point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
        points.append(point)
        logger.info(f"Точка добавлена: IOA={ioa}, тип={c104.Type.C_SE_NC_1}")
    
    logger.info("Запуск сервера...")
    server.start()
    logger.info("Сервер работает, ожидание данных...")
    
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "СЕРВЕР"))
    monitor_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Остановка сервера по прерыванию...")
    finally:
        stop_event.set()
        monitor_thread.join(timeout=5)
        logger.info(f"Поток завершён, is_alive={monitor_thread.is_alive()}")
        server.stop()
        logger.info("Сервер остановлен")

if __name__ == "__main__":
    main()
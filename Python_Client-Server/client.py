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
    format='%(asctime)s - %(levelname)s - [CLIENT] - %(message)s',
    handlers=[
        logging.FileHandler('client.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

resource_logger = setup_resource_logger()

def save_resource_data(cpu_percent, memory_percent, timestamp, filename=r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\client_resources.json"):
    logger.debug(f"Сохранение данных, filename={filename}")
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
            except json.JSONDecodeError:
                logger.warning(f"Файл {filename} повреждён, создаём новый")
                existing_data = []
        existing_data = [d for d in existing_data if d['timestamp'] != timestamp]
        existing_data.append(data)
        temp_file = filename + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        os.replace(temp_file, filename)
        logger.info(f"Данные сохранены в {filename}: {data}")
        resource_logger.info(f"Клиент - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s")
    except Exception as e:
        logger.error(f"Ошибка сохранения в {filename}: {str(e)}", exc_info=True)
        raise

def monitor_resources(stop_event, prefix="КЛИЕНТ"):
    global start_time
    logger.debug(f"Запуск monitor_resources для {prefix}")
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        timestamp = int(time.time() - start_time)
        save_resource_data(cpu_percent, memory_percent, timestamp)
        logger.info(f"Начальные данные ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%, Время={timestamp}s")
    except Exception as e:
        logger.error(f"Ошибка начальной записи: {str(e)}", exc_info=True)
        return
    
    while not stop_event.is_set():
        try:
            logger.debug(f"Цикл monitor_resources активен")
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            timestamp = int(time.time() - start_time)
            save_resource_data(cpu_percent, memory_percent, timestamp)
            logger.info(f"Данные ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%, Время={timestamp}s")
            if cpu_percent > 80 or memory_percent > 80:
                logger.warning(f"Высокая загрузка ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
        except Exception as e:
            logger.error(f"Ошибка в monitor_resources: {str(e)}", exc_info=True)
        time.sleep(5)

def main():
    global start_time
    client_json = r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\client_resources.json"
    if os.path.exists(client_json):
        try:
            os.remove(client_json)
            logger.info(f"Удалён старый файл {client_json}")
        except Exception as e:
            logger.error(f"Ошибка удаления {client_json}: {str(e)}", exc_info=True)
    
    try:
        max_wait = 10  # Ждать до 10 секунд
        wait_time = 0
        while not os.path.exists(r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\start_time.json") and wait_time < max_wait:
            logger.debug(f"Ожидание start_time.json, попытка {wait_time + 1}/{max_wait}")
            time.sleep(1)
            wait_time += 1
        if not os.path.exists(r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\start_time.json"):
            start_time = time.time()
            logger.warning(f"start_time.json не найден после {max_wait} секунд, использую текущее время: {start_time}")
        else:
            with open(r"C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server\start_time.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                start_time = data["start_time"]
            logger.info(f"start_time загружен: {start_time}")
    except Exception as e:
        start_time = time.time()
        logger.error(f"Ошибка чтения start_time.json: {str(e)}, использую текущее время: {start_time}")
    
    logger.info(f"Рабочая директория: {os.getcwd()}")
    
    try:
        save_resource_data(0.0, 0.0, 0, client_json)
        logger.info(f"Создан начальный файл {client_json}")
    except Exception as e:
        logger.error(f"Ошибка создания {client_json}: {str(e)}", exc_info=True)
    
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        logger.info(f"Типы c104: {[t for t in dir(c104.Type) if not t.startswith('_')]}")
        client = c104.Client()
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        station = connection.add_station(common_address=1)
        points = []
        for ioa in range(0, 10):
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
            logger.info(f"Точка добавлена: IOA={ioa}")
        
        logger.info("Подключение к серверу...")
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts and not connection.is_connected:
            try:
                logger.debug(f"Попытка подключения {attempt + 1}/{max_attempts}, состояние: {connection.is_connected}")
                time.sleep(2)
                attempt += 1
            except Exception as e:
                logger.error(f"Ошибка при подключении: {str(e)}", exc_info=True)
        if not connection.is_connected:
            logger.error(f"Не удалось подключиться к серверу после {max_attempts} попыток")
            return
        
        client.start()
        if not client.is_running:
            logger.error("Клиент не запущен")
            return
        
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "КЛИЕНТ"))
        monitor_thread.start()
        logger.info("Поток monitor_resources запущен")
        
        duration = 300  # 5 минут
        end_time = start_time + duration
        while time.time() < end_time:
            start_loop = time.time()
            for point in points:
                value = random.uniform(0.0, 1.0)
                point.value = value
                logger.debug(f"Передача: IOA={point.io_address}, значение={value:.3f}")
                point.transmit(cause=c104.Cot.ACTIVATION)
                logger.info(f"Отправлено: IOA={point.io_address}, значение={value:.3f}")
            elapsed = time.time() - start_loop
            if elapsed < 1.0:
                time.sleep(max(0, 1.0 - elapsed))
        
    except Exception as e:
        logger.error(f"Общая ошибка клиента: {str(e)}", exc_info=True)
    finally:
        stop_event.set()
        if monitor_thread:
            monitor_thread.join(timeout=5)
            logger.info(f"Поток завершён, is_alive={monitor_thread.is_alive()}")
        if 'client' in locals():
            logger.info("Остановка клиента...")
            client.stop()

if __name__ == "__main__":
    main()
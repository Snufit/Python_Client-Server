# https://github.com/Snufit/Python_Client-Server.git
# https://iec104-python.readthedocs.io/latest/python/connection.html
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

# Добавление пути к директории с logging_config.py
logging_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logging_config.py'))
print(f"Проверяемый путь к logging_config.py: {logging_config_path}")
if not os.path.exists(logging_config_path):
    print(f"Ошибка: файл {logging_config_path} не существует")
sys.path.append(os.path.dirname(logging_config_path))
from logging_config import setup_resource_logger

# Создание директории logs, если она не существует
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [CLIENT] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'client.log'), mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка логгера ресурсов для клиента
resource_logger = setup_resource_logger(log_dir=log_dir, log_filename="resource_usage_client.log")

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="client_resources.json"):
    """Сохраняет данные ЦП и ОЗУ в JSON и resource_usage_client.log"""
    data = {
        "timestamp": timestamp,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "overload": cpu_percent > 80 or memory_percent > 80
    }
    try:
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        existing_data.append(data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        resource_logger.info(f"Клиент - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s, Перегрузка: {data['overload']}")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов: {str(e)}", exc_info=True)

def monitor_resources(stop_event, prefix="КЛИЕНТ"):
    """Мониторинг загрузки ЦП и ОЗУ"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    save_resource_data(cpu_percent, memory_percent, 0)
    logger.info(f"Базовое использование ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
    
    while not stop_event.is_set():
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        timestamp = int(time.time() - start_time)
        save_resource_data(cpu_percent, memory_percent, timestamp)
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"Высокая загрузка ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
        time.sleep(5)

def main():
    global start_time
    start_time = time.time()
    
    # Удаление старого файла ресурсов
    if os.path.exists("client_resources.json"):
        os.remove("client_resources.json")
    
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        client = c104.Client()
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        station = connection.add_station(common_address=1)
        points = []
        for ioa in range(1000):
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
            logger.info(f"Точка добавлена: IOA={ioa}, тип=C_SE_NC_1")

        logger.info("Подключение к серверу...")
        client.start()
        time.sleep(5)
        
        if not client.is_running or not connection.is_connected:
            logger.error(f"Не удалось подключиться к серверу. Состояние клиента: is_running={client.is_running}, is_connected={connection.is_connected}")
            return
        
        logger.info("Подключение успешно установлено")
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "КЛИЕНТ"))
        monitor_thread.start()
        
        # Отправка данных
        duration = 3600
        end_time = start_time + duration
        batch_size = 100
        while time.time() < end_time:
            start_loop = time.time()
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                for point in batch:
                    value = random.uniform(0.0, 100.0)
                    point.value = value
                    logger.debug(f"Подготовка к передаче: IOA={point.io_address}, значение={value:.3f}")
                    point.transmit(cause=c104.Cot.ACTIVATION)
                    logger.info(f"Отправлено: IOA={point.io_address}, значение={value:.3f}")  
            elapsed = time.time() - start_loop
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        
    except Exception as e:
        logger.error(f"Ошибка клиента: {str(e)}", exc_info=True)
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'client' in locals():
            logger.info("Остановка клиента...")
            client.stop()

if __name__ == "__main__":
    main()
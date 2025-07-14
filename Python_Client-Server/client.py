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
sys.path.append(r'C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server')
from logging_config import setup_resource_logger

# Настройка логирования в файл (перезапись) и консоль
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [CLIENT] - %(message)s',
    handlers=[
        logging.FileHandler('client.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка логгера ресурсов
resource_logger = setup_resource_logger()

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="client_resources.json"):
    """Сохраняет данные ЦП и ОЗУ в JSON и resource_usage.log"""
    logger.debug("Вход в save_resource_data")
    data = {"timestamp": timestamp, "cpu_percent": cpu_percent, "memory_percent": memory_percent}
    try:
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        existing_data.append(data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        logger.debug(f"Сохранены данные ресурсов в {filename}: {data}")
        resource_logger.info(f"Клиент - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов: {str(e)}")

def monitor_resources(stop_event, prefix="КЛИЕНТ"):
    """Мониторинг загрузки ЦП и ОЗУ"""
    logger.debug(f"Запуск monitor_resources для {prefix}")

    # Базовые значения до запуска
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
        logger.info(f"Использование ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"Высокая загрузка ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
        time.sleep(5)

def main():
    global start_time
    start_time = time.time()
    
    # Инициализация переменных
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        # Вывод доступных типов
        logger.info(f"Доступные типы c104: {[t for t in dir(c104.Type) if not t.startswith('_')]}")
        
        # Создание клиента
        client = c104.Client()
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        station = connection.add_station(common_address=1)
        points = []
        for ioa in range(1000): 
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
            logger.info(f"Точка добавлена: IOA={ioa}, тип=C_SE_NC_1")
        
        # Подключение
        logger.info("Подключение к серверу...")
        client.start()
        time.sleep(15)
        
        if not client.is_running:
            logger.error("Не удалось подключиться к серверу")
            return
        
        if connection.is_connected:
            logger.info("Подключение успешно установлено")
        else:
            logger.error("Подключение не установлено")
            return
        
        # Запуск мониторинга
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "КЛИЕНТ"))
        monitor_thread.start()
        
        # Отправка данных (1000 измерений в секунду в течение 1 часа)
        duration = 3600  
        end_time = start_time + duration
        while time.time() < end_time:
            start_loop = time.time()
            for point in points:
                value = random.uniform(0.0, 1.0)
                point.value = value
                logger.debug(f"Подготовка к передаче: IOA={point.io_address}, значение={value:.3f}")
                point.transmit(cause=c104.Cot.ACTIVATION)
                logger.info(f"Отправлено: IOA={point.io_address}, значение={value:.3f}")
            
            elapsed = time.time() - start_loop
            if elapsed < 1.0:
                time.sleep(max(0, 1.0 - elapsed)) 
        
    except Exception as e:
        logger.error(f"Ошибка клиента: {str(e)}")
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'client' in locals():
            logger.info("Остановка клиента...")
            client.stop()

if __name__ == "__main__":
    main()
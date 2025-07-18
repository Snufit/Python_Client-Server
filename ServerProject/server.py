# -*- coding: utf-8 -*-
import c104
import time
import logging
import psutil
import threading
import json
import os
import sys
logging_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logging_config.py'))
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
    format='%(asctime)s - %(levelname)s - [SERVER] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'server.log'), mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройка логгера ресурсов для сервера
resource_logger = setup_resource_logger(log_dir=log_dir, log_filename="resource_usage_server.log")

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="server_resources.json"):
    """Сохраняет данные ЦП и ОЗУ в JSON и resource_usage_server.log"""
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
        resource_logger.info(f"Сервер - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s, Перегрузка: {data['overload']}")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов: {str(e)}", exc_info=True)

def monitor_resources(stop_event, prefix="СЕРВЕР"):
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
        time.sleep(0.5)

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных для точки"""
    if point.io_address % 100 == 0:  # Логировать каждую 100-ю точку
        logger.info(f"Получено: IOA={point.io_address}, значение={point.value:.3f}, качество={point.quality}")
    return c104.ResponseState.SUCCESS

def main():
    global start_time
    start_time = time.time()
    
    # Удаление старого файла ресурсов
    if os.path.exists("server_resources.json"):
        os.remove("server_resources.json")
    
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        server = c104.Server(ip="127.0.0.1", port=2404)
        station = server.add_station(common_address=1)
        for ioa in range(1000):
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            point.on_receive(on_new_data)
            logger.debug(f"Точка добавлена: IOA={ioa}, тип=C_SE_NC_1")
        
        logger.info("Запуск сервера...")
        server.start()
        
        if not server.is_running:
            logger.error("Не удалось запустить сервер")
            return
        
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "СЕРВЕР"))
        monitor_thread.start()
        
        logger.info("Сервер работает, ожидание данных...")
        while time.time() - start_time < 3600:  # 1 час
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Ошибка сервера: {str(e)}", exc_info=True)
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'server' in locals():
            logger.info("Остановка сервера...")
            server.stop()

if __name__ == "__main__":
    main()
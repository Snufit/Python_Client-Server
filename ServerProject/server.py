﻿# -*- coding: utf-8 -*-
import c104
import time
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
    format='%(asctime)s - %(levelname)s - [SERVER] - %(message)s',
    handlers=[
        logging.FileHandler('server.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Диагностика запуска
logger.debug("Server script started")

# Настройка логгера ресурсов
resource_logger = setup_resource_logger()

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="server_resources.json"):
    """Сохраняет данные ЦП и ОЗУ в JSON и resource_usage.log"""
    logger.debug("Entering save_resource_data")
    data = {"timestamp": timestamp, "cpu_percent": cpu_percent, "memory_percent": memory_percent}
    try:
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        existing_data.append(data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        logger.debug(f"Saved resource data to {filename}: {data}")
        resource_logger.info(f"Server - CPU: {cpu_percent:.1f}%, RAM: {memory_percent:.1f}%, Timestamp: {timestamp}s")
    except Exception as e:
        logger.error(f"Error saving resource data: {str(e)}")

def monitor_resources(stop_event, prefix="SERVER"):
    """Мониторинг загрузки ЦПУ и ОЗУ"""
    logger.debug(f"Starting monitor_resources for {prefix}")
    # Базовые значения до запуска
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    save_resource_data(cpu_percent, memory_percent, 0)
    logger.info(f"Baseline resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
    
    while not stop_event.is_set():
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        timestamp = int(time.time() - start_time)
        save_resource_data(cpu_percent, memory_percent, timestamp)
        logger.info(f"Resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"High resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        time.sleep(5)

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных для точки"""
    logger.debug(f"Point handler triggered for IOA={point.io_address}")
    logger.info(f"Received: IOA={point.io_address}, value={point.value:.3f}, quality={point.quality}")
    return c104.ResponseState.SUCCESS

def main():
    global start_time
    start_time = time.time()
    logger.debug("Server main started")
    
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        logger.debug("Before creating server")
        server = c104.Server(ip="127.0.0.1", port=2404)
        logger.debug("Server created")
        station = server.add_station(common_address=1)
        logger.info(f"Station created with common_address=1")
        
        points = []
        for ioa in range(1000, 1005):  # 5 точек
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            point.on_receive(on_new_data)
            points.append(point)
            logger.info(f"Point added: IOA={ioa}, type=C_SE_NC_1")
        
        logger.info("Starting server...")
        server.start()
        
        if not server.is_running:
            logger.error("Failed to start server")
            return
        
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "SERVER"))
        monitor_thread.start()
        
        logger.info("Server is running, waiting for data...")
        start_time = time.time()
        while time.time() - start_time < 75:
            logger.debug("Server still running...")
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'server' in locals():
            logger.info("Stopping server...")
            server.stop()

if __name__ == "__main__":
    main()
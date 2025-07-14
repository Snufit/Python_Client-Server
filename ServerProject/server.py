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
logger.debug("Скрипт сервера запущен")

# Настройка логгера ресурсов
resource_logger = setup_resource_logger()

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="server_resources.json"):
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
        resource_logger.info(f"Сервер - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов: {str(e)}")

def monitor_resources(stop_event, prefix="СЕРВЕР"):
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

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных для точки"""
    logger.debug(f"Обработчик точки активирован для IOA={point.io_address}")
    logger.info(f"Получено: IOA={point.io_address}, значение={point.value:.3f}, качество={point.quality}")
    return c104.ResponseState.SUCCESS

def main():
    global start_time
    start_time = time.time()
    logger.debug("Запуск main сервера")
    
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        logger.debug("Перед созданием сервера")
        server = c104.Server(ip="127.0.0.1", port=2404)
        logger.debug("Сервер создан")
        station = server.add_station(common_address=1)
        logger.info(f"Станция создана с common_address=1")
        
        points = []
        for ioa in range(1000): 
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            point.on_receive(on_new_data)
            points.append(point)
            logger.info(f"Точка добавлена: IOA={ioa}, тип=C_SE_NC_1")
        
        logger.info("Запуск сервера...")
        server.start()
        
        if not server.is_running:
            logger.error("Не удалось запустить сервер")
            return
        
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "СЕРВЕР"))
        monitor_thread.start()
        
        logger.info("Сервер работает, ожидание данных...")
        start_time = time.time()
        while time.time() - start_time < 3600:  # 1 час
            logger.debug("Сервер продолжает работу...")
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Ошибка сервера: {str(e)}")
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'server' in locals():
            logger.info("Остановка сервера...")
            server.stop()

if __name__ == "__main__":
    main()
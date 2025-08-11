# -*- coding: utf-8 -*-
import c104
import time
import logging
import psutil
from multiprocessing import Process, Event
import json
import os

# Создание директории logs, если она не существует
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования для сервера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [SERVER] - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'server.log'), mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Логгер для ресурсов сервера
resource_logger = logging.getLogger('resource')
resource_logger.setLevel(logging.INFO)
resource_handler = logging.FileHandler(os.path.join(log_dir, 'resource_usage_server.log'), mode='w', encoding='utf-8')
resource_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
resource_logger.addHandler(resource_handler)

def save_resource_data(cpu_percent, memory_percent, timestamp, filename=os.path.join(log_dir, 'resource_usage_server.json')):
    """Сохраняет данные ЦП и ОЗУ в JSON и resource_usage_server.log"""
    data = {
        "timestamp": timestamp,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "overload": cpu_percent > 80 or memory_percent > 80
    }
    try:
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        existing_data.append(data)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        resource_logger.info(f"Сервер - ЦП: {cpu_percent:.1f}%, ОЗУ: {memory_percent:.1f}%, Время: {timestamp}s, Перегрузка: {data['overload']}")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных ресурсов: {str(e)}", exc_info=True)

def monitor_resources(stop_event, prefix="Сервер"):
    """Мониторинг загрузки ЦП и ОЗУ"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    save_resource_data(cpu_percent, memory_percent, 0)
    logger.info(f"Базовое использование ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")
    
    start_time = time.time()
    while not stop_event.is_set():
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        timestamp = int(time.time() - start_time)
        save_resource_data(cpu_percent, memory_percent, timestamp)
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"Высокая загрузка ресурсов ({prefix}): ЦП={cpu_percent:.1f}%, ОЗУ={memory_percent:.1f}%")

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных для точки"""
    if point.io_address % 100 == 0:  # Логировать каждую 100-ю точку
        logger.info(f"Получено: IOA={point.io_address}, значение={point.value:.3f}, качество={point.quality}")
    return c104.ResponseState.SUCCESS

def main():
    # Удаление старого файла ресурсов
    if os.path.exists(os.path.join(log_dir, 'resource_usage_server.json')):
        os.remove(os.path.join(log_dir, 'resource_usage_server.json'))
    
    stop_event = Event()
    monitor_process = None
    
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
        
        monitor_process = Process(target=monitor_resources, args=(stop_event, "Сервер"))
        monitor_process.start()
        
        logger.info("Сервер работает, ожидание данных...")
        time.sleep(3600)  # 1 час
        
    except Exception as e:
        logger.error(f"Ошибка сервера: {str(e)}", exc_info=True)
    finally:
        stop_event.set()
        if monitor_process is not None:
            monitor_process.join()
        if 'server' in locals():
            logger.info("Остановка сервера...")
            server.stop()

if __name__ == "__main__":
    main()
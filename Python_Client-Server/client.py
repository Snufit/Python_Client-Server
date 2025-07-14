import c104
import time
import random
import logging
import psutil
import threading
import json
import os
import webbrowser

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [CLIENT] - %(message)s')
logger = logging.getLogger(__name__)

def save_resource_data(cpu_percent, memory_percent, timestamp, filename="client_resources.json"):
    """Сохраняет данные ЦП и ОЗУ в JSON"""
    data = {
        "timestamp": timestamp,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent
    }
    try:
        # Читаем существующие данные
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing_data = json.load(f)
        # Добавляем новую точку
        existing_data.append(data)
        # Сохраняем обновлённые данные
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
        logger.debug(f"Saved resource data to {filename}: {data}")
    except Exception as e:
        logger.error(f"Error saving resource data: {str(e)}")

def monitor_resources(stop_event, prefix="CLIENT"):
    """Мониторинг загрузки ЦПУ и ОЗУ"""
    # Базовые значения до запуска
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    save_resource_data(cpu_percent, memory_percent, 0)  # t=0
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

def main():
    global start_time
    start_time = time.time()
    
    # Инициализация переменных
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        # Открытие HTML-страницы
        html_path = os.path.abspath("resource_usage.html")
        webbrowser.open(f"file://{html_path}")
        logger.info(f"Opened visualization at {html_path}")
        
        # Вывод доступных типов
        logger.info(f"Available c104 types: {[t for t in dir(c104.Type) if not t.startswith('_')]}")
        
        # Создание клиента
        client = c104.Client()
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        station = connection.add_station(common_address=1)
        points = []
        for ioa in range(1000, 1005):  # 5 точек (можно изменить на 1000, 1010)
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
            logger.info(f"Point added: IOA={ioa}, type=C_SE_NC_1")
        
        # Подключение
        logger.info("Connecting to server...")
        client.start()
        time.sleep(15)
        
        if not client.is_running:
            logger.error("Failed to connect to server")
            return
        
        if connection.is_connected:
            logger.info("Connection established successfully")
        else:
            logger.error("Connection not established")
            return
        
        # Запуск мониторинга
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "CLIENT"))
        monitor_thread.start()
        
        # Отправка данных
        for i in range(60):
            start_loop = time.time()
            for point in points:
                value = random.uniform(0.0, 1.0)
                point.value = value
                logger.debug(f"Preparing to transmit: IOA={point.io_address}, value={value:.3f}")
                point.transmit(cause=c104.Cot.ACTIVATION)
                logger.info(f"Sent: IOA={point.io_address}, value={value:.3f}")
            
            elapsed = time.time() - start_loop
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        
    except Exception as e:
        logger.error(f"Client error: {str(e)}")
    finally:
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'client' in locals():
            logger.info("Stopping client...")
            client.stop()

if __name__ == "__main__":
    main()
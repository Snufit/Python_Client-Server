# -*- coding: utf-8 -*-
import c104
import time
import random
import logging
import psutil
import threading

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [CLIENT] - %(message)s')
logger = logging.getLogger(__name__)

def monitor_resources(stop_event, prefix="CLIENT"):
    """Мониторинг загрузки ЦПУ и ОЗУ"""
    while not stop_event.is_set():
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        logger.info(f"Resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"High resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        time.sleep(5)  # Логируем каждые 5 секунд

def main():
    # Инициализация переменных для мониторинга
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        # Вывод доступных типов для отладки
        logger.info(f"Available c104 types: {[t for t in dir(c104.Type) if not t.startswith('_')]}")
        
        # Создание клиента
        client = c104.Client()
        
        # Создание соединения
        connection = client.add_connection(ip="127.0.0.1", port=2404)
        
        # Создание станции (Common Address = 1)
        station = connection.add_station(common_address=1)
        points = []
        for ioa in range(1000, 1005):  # 5 точек
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
            logger.info(f"Point added: IOA={ioa}, type=C_SE_NC_1")
        
        # Подключение к серверу
        logger.info("Connecting to server...")
        client.start()
        
        # Задержка для ожидания готовности сервера
        time.sleep(15)
        
        if not client.is_running:
            logger.error("Failed to connect to server")
            return
        
        if connection.is_connected:
            logger.info("Connection established successfully")
        else:
            logger.error("Connection not established")
            return
        
        # Запуск мониторинга ресурсов в отдельном потоке
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "CLIENT"))
        monitor_thread.start()
        
        # Отправка измерений каждую секунду в течение 60 секунд
        for i in range(60):
            start_time = time.time()
            for point in points:
                # Генерация значения float (0.0 до 1.0)
                value = random.uniform(0.0, 1.0)
                point.value = value
                logger.debug(f"Preparing to transmit: IOA={point.io_address}, value={value:.3f}")
                point.transmit(cause=c104.Cot.ACTIVATION)
                logger.info(f"Sent: IOA={point.io_address}, value={value:.3f}")
            
            # Синхронизация для отправки каждую секунду
            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        
    except Exception as e:
        logger.error(f"Client error: {str(e)}")
    finally:
        # Остановка мониторинга и клиента
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'client' in locals():
            logger.info("Stopping client...")
            client.stop()

if __name__ == "__main__":
    main()
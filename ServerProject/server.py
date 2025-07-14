# -*- coding: utf-8 -*-
import c104
import time
import logging
import psutil
import threading

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [SERVER] - %(message)s')
logger = logging.getLogger(__name__)

def monitor_resources(stop_event, prefix="SERVER"):
    """Мониторинг загрузки ЦПУ и ОЗУ"""
    while not stop_event.is_set():
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        logger.info(f"Resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        if cpu_percent > 80 or memory_percent > 80:
            logger.warning(f"High resource usage ({prefix}): CPU={cpu_percent:.1f}%, RAM={memory_percent:.1f}%")
        time.sleep(5)  # Логируем каждые 5 секунд

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных для точки"""
    logger.debug(f"Point handler triggered for IOA={point.io_address}")
    logger.info(f"Received: IOA={point.io_address}, value={point.value:.3f}, quality={point.quality}")
    return c104.ResponseState.SUCCESS

def main():
    # Инициализация переменных для мониторинга
    stop_event = threading.Event()
    monitor_thread = None
    
    try:
        # Создание сервера
        server = c104.Server(ip="127.0.0.1", port=2404)
        
        # Создание станции (Common Address = 1)
        station = server.add_station(common_address=1)
        logger.info(f"Station created with common_address=1")
        
        # Добавление информационных объектов (IOA 1000-1004)
        points = []
        for ioa in range(1000, 1005):  # 5 точек
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            point.on_receive(on_new_data)  # Регистрация обработчика для каждой точки
            points.append(point)
            logger.info(f"Point added: IOA={ioa}, type=C_SE_NC_1")
        
        # Запуск сервера
        logger.info("Starting server...")
        server.start()
        
        if not server.is_running:
            logger.error("Failed to start server")
            return
        
        # Запуск мониторинга ресурсов в отдельном потоке
        monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, "SERVER"))
        monitor_thread.start()
        
        logger.info("Server is running, waiting for data...")
        # Ожидание данных в течение 75 секунд
        start_time = time.time()
        while time.time() - start_time < 75:
            logger.debug("Server still running...")
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        # Остановка мониторинга и сервера
        stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join()
        if 'server' in locals():
            logger.info("Stopping server...")
            server.stop()

if __name__ == "__main__":
    main()
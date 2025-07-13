# -*- coding: utf-8 -*-
import c104
import time
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_new_data(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    """Обработчик новых данных от клиента"""
    logger.info(f"Received: IOA={point.io_address}, value={point.value}, quality={point.quality}, time={point.time}")
    return c104.ResponseState.SUCCESS

def main():
    try:
        # Создание сервера
        server = c104.Server(ip="127.0.0.1", port=2404)
        
        # Создание станции (Common Address = 1)
        station = server.add_station(common_address=1)
        logger.info(f"Station created with common_address=1")
        
        # Добавление информационных объектов (IOA 1000-1999)
        for ioa in range(1000, 2000):
            point = station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
            point.on_receive(on_new_data)  # Установка обработчика новых данных
            logger.info(f"Point added: IOA={ioa}, type=M_ME_NC_1")
        
        # Запуск сервера
        logger.info("Starting server...")
        server.start()
        
        if not server.is_running:
            logger.error("Failed to start server")
            return
        
        logger.info("Server is running, waiting for data...")
        # Ожидание данных в течение 80 секунд
        start_time = time.time()
        while time.time() - start_time < 80:
            logger.debug("Server still running...")
            time.sleep(1)
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        # Остановка сервера
        if 'server' in locals():
            logger.info("Stopping server...")
            server.stop()

if __name__ == "__main__":
    main()
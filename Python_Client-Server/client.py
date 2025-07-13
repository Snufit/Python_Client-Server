# -*- coding: utf-8 -*-
import c104
import time
import random
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
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
        for ioa in range(1000, 1005):
            point = station.add_point(io_address=ioa, type=c104.Type.C_SE_NC_1)
            points.append(point)
        
        # Подключение к серверу
        logger.info("Connecting to server...")
        client.start()
        
        # Задержка для ожидания готовности сервера
        time.sleep(10)  # Увеличено до 10 секунд для синхронизации
        
        if not client.is_running:
            logger.error("Failed to connect to server")
            return
        
        # Отправка 1000 измерений каждую секунду в течение 60 секунд
        for _ in range(60):
            start_time = time.time()
            for point in points:
                # Генерация случайного значения в диапазоне 0.0–100.0 (float)
                value = random.uniform(0.0, 100.0)
                point.value = value
                point.transmit(cause=c104.Cot.SPONTANEOUS)
                logger.info(f"Sent: IOA={point.io_address}, value={value}")
            
            # Синхронизация для отправки каждую секунду
            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
        
    except Exception as e:
        logger.error(f"Client error: {str(e)}")
    finally:
        # Остановка клиента
        if 'client' in locals():
            logger.info("Stopping client...")
            client.stop()

if __name__ == "__main__":
    main()
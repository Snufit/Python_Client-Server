import logging
import os

def setup_resource_logger(log_dir="logs", log_filename="resource_usage.log"):
    """Настройка логгера для resource_usage.log с указанным именем файла"""
    # Создание директории для логов, если не существует
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    resource_logger = logging.getLogger('resource_usage')
    if not resource_logger.handlers:
        resource_handler = logging.FileHandler(os.path.join(log_dir, log_filename), mode='w', encoding='utf-8')
        resource_handler.setFormatter(logging.Formatter('%(asctime)s - [%(name)s] - %(message)s'))
        resource_logger.addHandler(resource_handler)
        resource_logger.setLevel(logging.INFO)
    return resource_logger
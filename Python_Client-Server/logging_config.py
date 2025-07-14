# -*- coding: utf-8 -*-
import logging

def setup_resource_logger():
    """Настройка логгера для resource_usage.log"""
    resource_logger = logging.getLogger('resource_usage')
    if not resource_logger.handlers:  
        resource_handler = logging.FileHandler('resource_usage.log', mode='w', encoding='utf-8')
        resource_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        resource_logger.addHandler(resource_handler)
        resource_logger.setLevel(logging.INFO)
    return resource_logger
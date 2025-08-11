# -*- coding: utf-8 -*-
import subprocess
import os
import time

def run_script(script_name):
    """Запускает указанный скрипт в отдельном процессе"""
    process = subprocess.Popen(
        ['python', script_name],
        cwd=r'C:\Users\Gleb\source\repos\Python_Client-Server\run_all',
        creationflags=subprocess.CREATE_NEW_CONSOLE  # Открывает новое окно консоли на Windows
    )
    return process

def main():
    # Запуск сервера
    print("Запуск сервера...")
    server_process = run_script('server.py')
    
    # Задержка перед запуском клиента
    time.sleep(5)
    
    # Запуск клиента
    print("Запуск клиента...")
    client_process = run_script('client.py')
    
    # Ожидание завершения клиента и сервера
    client_process.wait()
    server_process.terminate()  # Завершаем сервер, если он ещё работает
    server_process.wait()
    
    # Задержка перед запуском plot_log.py
    print("Ожидание 10 секунд перед построением графика...")
    time.sleep(10)
    
    # Запуск построения графика
    print("Запуск построения графика...")
    subprocess.run(['python', 'plot_log.py'], cwd=r'C:\Users\Gleb\source\repos\Python_Client-Server\logs')

if __name__ == "__main__":
    main()
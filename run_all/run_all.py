# -*- coding: utf-8 -*-
import subprocess
import time

def run_script(script_name, cwd):
    """Запускает указанный скрипт в отдельном процессе"""
    process = subprocess.Popen(
        ['python', script_name],
        cwd=cwd,
        creationflags=subprocess.CREATE_NEW_CONSOLE  # Открывает новое окно консоли на Windows
    )
    return process

def main():
    server_dir = r'C:\Users\Gleb\source\repos\Python_Client-Server\ServerProject'
    client_dir = r'C:\Users\Gleb\source\repos\Python_Client-Server\Python_Client-Server'
    logs_dir = r'C:\Users\Gleb\source\repos\Python_Client-Server\logs'

    # 1. Запуск сервера
    print("Запуск сервера...")
    server_process = run_script('server.py', server_dir)

    # 2. Задержка перед запуском клиента
    time.sleep(5)

    # 3. Запуск клиента
    print("Запуск клиента...")
    client_process = run_script('client.py', client_dir)

    # 4. Ожидание завершения клиента
    client_process.wait()

    # 5. Завершение сервера
    server_process.terminate()
    server_process.wait()

    # 6. Запуск построения графика после завершения обоих процессов
    print("Запуск построения графика...")
    subprocess.run(['python', 'plot_log.py'], cwd=logs_dir)

if __name__ == "__main__":
    main()

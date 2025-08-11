# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import json
import os  # Добавлен импорт os

# Загрузка данных из JSON
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"Файл {file_path} не найден")
        return []

client_data = load_data('logs/resource_usage_client.json')
server_data = load_data('logs/resource_usage_server.json')

# Построение графика
fig, ax = plt.subplots(2, 1, figsize=(12, 8))

# График для клиента
if client_data:
    client_times = [entry['timestamp'] for entry in client_data]
    client_cpu = [entry['cpu_percent'] for entry in client_data]
    client_mem = [entry['memory_percent'] for entry in client_data]
    ax[0].plot(client_times, client_cpu, label='ЦП клиента', color='blue')
    ax[0].plot(client_times, client_mem, label='ОЗУ клиента', color='green')
    ax[0].axhline(80, color='red', linestyle='--', label='Порог перегрузки')
    ax[0].set_title('Загрузка ресурсов клиента')
    ax[0].set_xlabel('Время (с)')
    ax[0].set_ylabel('%')
    ax[0].legend()
    ax[0].grid(True)

# График для сервера
if server_data:
    server_times = [entry['timestamp'] for entry in server_data]
    server_cpu = [entry['cpu_percent'] for entry in server_data]
    server_mem = [entry['memory_percent'] for entry in server_data]
    ax[1].plot(server_times, server_cpu, label='ЦП сервера', color='red')
    ax[1].plot(server_times, server_mem, label='ОЗУ сервера', color='orange')
    ax[1].axhline(80, color='red', linestyle='--', label='Порог перегрузки')
    ax[1].set_title('Загрузка ресурсов сервера')
    ax[1].set_xlabel('Время (с)')
    ax[1].set_ylabel('%')
    ax[1].legend()
    ax[1].grid(True)

plt.tight_layout()
plt.show()
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import re

# Парсинг лога (замените 'resource_usage.txt' на ваш файл)
with open('resource_usage.txt', 'r', encoding='utf-8') as f:
    log = f.read().splitlines()

client_times = []
client_cpu = []
client_mem = []
server_times = []
server_cpu = []
server_mem = []

for line in log:
    if "Клиент" in line:
        match = re.search(r"Время: (\d+)s", line)
        if match:
            time_s = int(match.group(1))
            cpu = float(re.search(r"ЦП: ([\d.]+)%", line).group(1))
            mem = float(re.search(r"ОЗУ: ([\d.]+)%", line).group(1))
            client_times.append(time_s)
            client_cpu.append(cpu)
            client_mem.append(mem)
    elif "Сервер" in line:
        match = re.search(r"Время: (\d+)s", line)
        if match:
            time_s = int(match.group(1))
            cpu = float(re.search(r"ЦП: ([\d.]+)%", line).group(1))
            mem = float(re.search(r"ОЗУ: ([\d.]+)%", line).group(1))
            server_times.append(time_s)
            server_cpu.append(cpu)
            server_mem.append(mem)

# Построение графика
fig, ax = plt.subplots(2, 1, figsize=(12, 8))

# График для клиента
ax[0].plot(client_times, client_cpu, label='ЦП клиента', color='blue')
ax[0].plot(client_times, client_mem, label='ОЗУ клиента', color='green')
ax[0].axhline(80, color='red', linestyle='--', label='Порог перегрузки')
ax[0].set_title('Загрузка ресурсов клиента')
ax[0].set_xlabel('Время (с)')
ax[0].set_ylabel('%')
ax[0].legend()
ax[0].grid(True)

# График для сервера
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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.get("https://my.mts-link.ru/j/120328607/24334684457")
time.sleep(2) # Даем странице немного загрузиться

# Путь к вашему файлу с куками
file_path = "cookie.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    parts = line.strip().split('\t')
    
    # Пропускаем пустые строки или строки с недостаточным количеством колонок
    if len(parts) < 4:
        continue
        
    name = parts[0]
    value = parts[1]
    domain = parts[2]
    path = parts[3]
    
    # Добавляем только куки, относящиеся к mts-link.ru
    if "mts-link.ru" in domain:
        cookie_dict = {
            'name': name,
            'value': value,
            'domain': domain,
            'path': path
        }
        
        try:
            driver.add_cookie(cookie_dict)
            print(f"Успешно добавлена кука: {name}")
        except Exception as e:
            print(f"Ошибка при добавлении куки {name}: {e}")

# ОБЯЗАТЕЛЬНО обновляем страницу после добавления куки
driver.refresh()
time.sleep(2)

try:
    # Ждём, пока элемент появится
    camera_btn = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "button.Button__btn___QAHvH.OdinControl__control___b1rRn"
        ))
    )
    print("Кнопка найдена:", camera_btn)
except Exception as e:
    print("Элемент не найден. Ошибка:", e)

input("Нажми Enter, чтобы закрыть браузер...")
driver.quit()
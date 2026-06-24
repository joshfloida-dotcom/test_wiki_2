import os
import time
import random
import requests

# ==========================================
# НАСТРОЙКИ СТЕГАНОГРАФИИ (VTEAM)
# ==========================================
MAGIC_MARKER = b'__VTEAM_DATA__'
SEPARATOR = b'|||'
WIKI_API_URL = "https://commons.wikimedia.org/w/api.php"

# Данные авторизации Википедии (из Secrets твоего репозитория)
USERNAME = os.getenv("WIKI_USER")
PASSWORD = os.getenv("WIKI_PASS")

# Точный список файлов скачанных из Smithsonian (в формате JPG)
SMITHSONIAN_FILES = [
    "ACM-acmobj-201400320001.jpg",
    "FS-7756_32.jpg",
    "NASM-NASM2013-02525.jpg",
    "NMAAHC-2010_19_1_001.jpg",
    "NMAH-JN2014-3625.jpg",
    "NMAH-JN2016-01951-000001.jpg",
    "ACM-acmobj-199400010001-r1.jpg",
    "ACM-acmobj-200400070001-r11.jpg",
    "NPM-1990_0207_1.jpg",
    "NPM-1998_2021_1_1j.jpg"
]

# Смитсоновский архив публикует данные в общественное достояние,
# поэтому используем CC0, чтобы загрузка выглядела абсолютно легально.
WIKI_LICENSE = "{{Cc-zero}}" 

def generate_wiki_page_text(original_filename):
    """Генерирует текст страницы с маскировкой под легитимную архивную загрузку."""
    return f"""== Summary ==
{{{{Information
|Description=Historical artifact / object from the Smithsonian Institution collection. Original ID: {original_filename}
|Source=Smithsonian Open Access
|Author=Smithsonian Institution
|Date=
|Permission=
|other_versions=
}}}}

== Licensing ==
{WIKI_LICENSE}

[[Category:Media from the Smithsonian Institution]]"""

def main():
    if not USERNAME or not PASSWORD:
        print("[!] Ошибка: Не заданы переменные окружения WIKI_USER или WIKI_PASS")
        return

    session = requests.Session()
    # Реалистичный User-Agent
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MediaWikiAssetUploader/1.2'})

    try:
        # Шаг 1: Логин на Википедии (Получаем Login Token)
        r1 = session.get(url=WIKI_API_URL, params={"action": "query", "meta": "tokens", "type": "login", "format": "json"}).json()
        login_token = r1["query"]["tokens"]["logintoken"]

        # Шаг 2: Авторизация
        r2 = session.post(WIKI_API_URL, data={
            "action": "login",
            "lgname": USERNAME,
            "lgpassword": PASSWORD,
            "lgtoken": login_token,
            "format": "json"
        }).json()
        
        if r2["login"]["result"] != "Success":
            print(f"[!] Ошибка авторизации: {r2['login'].get('reason', 'Неизвестная ошибка')}")
            return
        print("[+] Авторизация на МедиаВики успешна.")

        # Шаг 3: Получаем CSRF-токен
        r3 = session.get(url=WIKI_API_URL, params={"action": "query", "meta": "tokens", "type": "csrf", "format": "json"}).json()
        csrf_token = r3["query"]["tokens"]["csrftoken"]

        # Шаг 4: Конвейер обработки файлов (JPG)
        for i, filename in enumerate(SMITHSONIAN_FILES, start=1):
            config_url = f"https://raw.githubusercontent.com/joshfloida-dotcom/sni_test/refs/heads/main/tranco_lists/tranco_part_{i}.txt"
            
            # Предполагается, что картинки лежат в папке templates/
            local_image_path = f"templates/{filename}"
            wiki_filename = filename # Оставляем оригинальные музейные названия

            print(f"\n[*] Обработка пары №{i} ({filename})...")
            
            if not os.path.exists(local_image_path):
                print(f"[!] Ошибка: Локальный файл донора {local_image_path} не найден! Пропуск.")
                continue

            # 4.1 Скачиваем конфиг
            try:
                config_resp = session.get(config_url, timeout=15)
                config_resp.raise_for_status()
                secret_bytes = config_resp.content.strip()
                print(f"[+] Скачан конфиг sub_{i}.txt ({len(secret_bytes)} байт)")
            except Exception as e:
                print(f"[!] Не удалось скачать конфиг: {e}. Пропуск.")
                continue

            # 4.2 Сборка payload
            secret_filename = f"sub_{i}.txt".encode('utf-8')
            payload = MAGIC_MARKER + secret_filename + SEPARATOR + secret_bytes

            # 4.3 Чтение JPG донора и склейка
            with open(local_image_path, 'rb') as f:
                image_bytes = f.read()

            final_container_bytes = image_bytes + payload
            temp_output = "temp_stego_upload.jpg" # Расширение изменено на .jpg

            with open(temp_output, 'wb') as f:
                f.write(final_container_bytes)

            # Формируем музейное описание
            page_text = generate_wiki_page_text(filename)

            # Имитация человеческой паузы перед запросом (от 10 до 25 секунд)
            if i > 1:
                sleep_time = random.randint(10, 25)
                print(f"[*] Ожидание {sleep_time} сек. для защиты от антифлуда...")
                time.sleep(sleep_time)

            # 4.4 Отправка в API
            print(f"[*] Загрузка {wiki_filename} на Викисклад...")
            with open(temp_output, 'rb') as file_data:
                upload_params = {
                    "action": "upload",
                    "filename": wiki_filename,
                    "token": csrf_token,
                    "text": page_text,
                    "ignorewarnings": "1",
                    "comment": "Importing high resolution artifact imagery from Smithsonian Open Access archive.",
                    "format": "json"
                }
                # Принудительно передаем корректный MIME-тип 'image/jpeg'
                files_payload = {"file": (wiki_filename, file_data, "image/jpeg")}
                r4 = session.post(WIKI_API_URL, files=files_payload, data=upload_params).json()
                
                result = r4.get("upload", {}).get("result")
                if result == "Success":
                    print(f"[+] Успешно! Файл {wiki_filename} загружен.")
                else:
                    print(f"[-] Ошибка загрузки {wiki_filename}. Ответ API: {r4}")

            if os.path.exists(temp_output):
                os.remove(temp_output)

    except Exception as e:
        print(f"[!] Критическая ошибка в работе скрипта: {e}")

if __name__ == "__main__":
    main()

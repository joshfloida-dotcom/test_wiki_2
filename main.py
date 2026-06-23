import os
import time
import random
import requests

# ==========================================
# НАСТРОЙКИ СТЕГАНОГРАФИИ (ТВОИ СТАНДАРТЫ)
# ==========================================
MAGIC_MARKER = b'__VTEAM_DATA__'
SEPARATOR = b'|||'
WIKI_API_URL = "https://commons.wikimedia.org/w/api.php"

# Данные авторизации Википедии (из Secrets твоего репозитория)
USERNAME = os.getenv("WIKI_USER")
PASSWORD = os.getenv("WIKI_PASS")

# Новое префикс-имя, полностью соответствующее типу картинок (PNG ассеты)
WIKI_FILE_PREFIX = "Metallic_car_paint_texture"

# ==========================================
# НАСТРОЙКИ ЛИЦЕНЗИРОВАНИЯ И ОПИСАНИЯ ФАЙЛОВ
# ==========================================
WIKI_LICENSE = "{{CC-BY-SA-4.0}}" 

def generate_wiki_page_text(description, author, license_template):
    """Генерирует текст страницы с маскировочными категориями для 3D-ассетов."""
    return f"""== Summary ==
{{{{Information
|Description={description}
|Source={{{{own}}}}
|Author={author}
|Date=
|Permission=
|other_versions=
}}}}

== Licensing ==
{license_template}

[[Category:Textures]]
[[Category:Procedural generation]]"""

def main():
    if not USERNAME or not PASSWORD:
        print("[!] Ошибка: Не заданы переменные окружения WIKI_USER или WIKI_PASS")
        return

    session = requests.Session()
    # Реалистичный User-Agent, чтобы не выглядеть как подозрительный бот
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MediaWikiAssetUploader/1.1'})

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

        # Шаг 4: Конвейер обработки первых 10 файлов (PNG)
        for i in range(1, 11):
            config_url = f"https://raw.githubusercontent.com/capitainblack/freetm3/refs/heads/main/configs/sub_{i}.txt"
            
            # Твои новые исходные картинки
            local_image_path = f"templates/car_pain_texture_{i}.png"
            # Финальное имя на Вики теперь тоже строго .png
            wiki_filename = f"{WIKI_FILE_PREFIX}_{i:02d}.png" 

            print(f"\n[*] Обработка пары №{i}...")
            
            if not os.path.exists(local_image_path):
                print(f"[!] Ошибка: Локальный шаблон {local_image_path} не найден! Пропуск.")
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

            # 4.3 Чтение PNG донора и склейка
            with open(local_image_path, 'rb') as f:
                image_bytes = f.read()

            final_container_bytes = image_bytes + payload
            temp_output = "temp_stego_upload.png" # Расширение изменено на .png

            with open(temp_output, 'wb') as f:
                f.write(final_container_bytes)

            # Стандартное конвейерное описание
            file_description = f"Procedural car paint texture shader asset, variant {i:02d}."
            page_text = generate_wiki_page_text(file_description, USERNAME, WIKI_LICENSE)

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
                    "comment": "Update procedural PBR texture maps for automotive rendering.",
                    "format": "json"
                }
                # Принудительно передаем корректный MIME-тип 'image/png'
                files_payload = {"file": (wiki_filename, file_data, "image/png")}
                r4 = session.post(WIKI_API_URL, files=files_payload, data=upload_params).json()
                
                result = r4.get("upload", {}).get("result")
                if result == "Success":
                    print(f"[+] Успешно! Файл {wiki_filename} обновлен.")
                else:
                    print(f"[-] Ошибка загрузки {wiki_filename}. Ответ API: {r4}")

            if os.path.exists(temp_output):
                os.remove(temp_output)

        # ==========================================
        # ОБРАБОТКА 11-Й КАРТИНКИ (TOR BRIDGES)
        # ==========================================
        sleep_time_11 = random.randint(20, 40)
        print(f"\n[*] Пауза {sleep_time_11} сек. перед финальным ассетом...")
        time.sleep(sleep_time_11)

        print("[*] Обработка специальной картинки №11 (Tor Bridges)...")
        local_image_path_11 = "templates/car_pain_texture_11.png"
        # ИСПРАВЛЕНО: Никаких "Make_new_file.jpg". Теперь это идеальное продолжение серии.
        wiki_filename_11 = f"{WIKI_FILE_PREFIX}_11.png" 

        if not os.path.exists(local_image_path_11):
            print(f"[!] Ошибка: Локальный шаблон {local_image_path_11} не найден! Пропуск.")
        else:
            bridge_urls = [
                "https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridge/webtunnel.txt",
                "https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridge/vanilla.txt",
                "https://raw.githubusercontent.com/Delta-Kronecker/Tor-Bridges-Collector/refs/heads/main/bridge/obfs4.txt"
            ]
            
            combined_bridges_content = b""
            download_success = True

            for url in bridge_urls:
                try:
                    resp = session.get(url, timeout=15)
                    resp.raise_for_status()
                    if combined_bridges_content and resp.content:
                        combined_bridges_content += b"\n"
                    combined_bridges_content += resp.content.strip()
                    print(f"[+] Успешно скачан файл: {url.split('/')[-1]}")
                except Exception as e:
                    print(f"[!] Ошибка при скачивании {url}: {e}")
                    download_success = False
                    break

            if download_success and len(combined_bridges_content) > 0:
                secret_filename_11 = b"bridges.txt"
                payload_11 = MAGIC_MARKER + secret_filename_11 + SEPARATOR + combined_bridges_content

                with open(local_image_path_11, 'rb') as f:
                    image_bytes_11 = f.read()

                final_container_bytes_11 = image_bytes_11 + payload_11
                temp_output_11 = "temp_stego_upload_11.png" 

                with open(temp_output_11, 'wb') as f:
                    f.write(final_container_bytes_11)

                # Описание абсолютно идентично остальным — ни единого внешнего отличия
                file_description_11 = f"Procedural car paint texture shader asset, variant 11."
                page_text_11 = generate_wiki_page_text(file_description_11, USERNAME, WIKI_LICENSE)

                print(f"[*] Загрузка {wiki_filename_11} на Викисклад...")
                with open(temp_output_11, 'rb') as file_data:
                    upload_params_11 = {
                        "action": "upload",
                        "filename": wiki_filename_11,
                        "token": csrf_token,
                        "text": page_text_11,
                        "ignorewarnings": "1",
                        "comment": "Update procedural PBR texture maps for automotive rendering.",
                        "format": "json"
                    }
                    # MIME-тип изменен на image/png
                    files_payload_11 = {"file": (wiki_filename_11, file_data, "image/png")}
                    r4_11 = session.post(WIKI_API_URL, files=files_payload_11, data=upload_params_11).json()
                    
                    result_11 = r4_11.get("upload", {}).get("result")
                    if result_11 == "Success":
                        print(f"[+] Успешно! Файл {wiki_filename_11} обновлен.")
                    else:
                        print(f"[-] Ошибка загрузки {wiki_filename_11}. Ответ API: {r4_11}")

                if os.path.exists(temp_output_11):
                    os.remove(temp_output_11)

    except Exception as e:
        print(f"[!] Критическая ошибка в работе скрипта: {e}")

if __name__ == "__main__":
    main()

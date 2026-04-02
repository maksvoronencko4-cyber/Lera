"""
🖥️ УПРАВЛЕНИЕ ПК v3.0 — С умным закрытием вкладок по домену
"""
import os
import sys
import subprocess
import webbrowser
import time
from typing import Optional, Dict, List, Tuple

# Настройки
SEARCH_ENGINE = "https://www.google.com/search?q="
SCREENSHOT_PATH = "screenshots"

# Базовые известные программы
KNOWN_PROGRAMS: Dict[str, str] = {
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "opera": "opera",
    "браузер": "chrome",
    "блокнот": "notepad",
    "notepad": "notepad",
    "калькулятор": "calc",
    "calculator": "calc",
    "проводник": "explorer",
    "explorer": "explorer",
    "командная строка": "cmd",
    "cmd": "cmd",
    "powershell": "powershell",
    "диспетчер задач": "taskmgr",
    "task manager": "taskmgr",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "paint": "mspaint",
    "telegram": "telegram",
    "discord": "discord",
    "teams": "teams",
}

# Базовые сайты — теперь с доменами!
KNOWN_SITES: Dict[str, str] = {
    "google": "https://www.google.com",
    "гугл": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "ютуб": "https://www.youtube.com",
    "vk": "https://vk.com",
    "вк": "https://vk.com",
    "вконтакте": "https://vk.com",
    "telegram": "https://web.telegram.org",
    "телеграм": "https://web.telegram.org",
    "github": "https://github.com",
    "гитхаб": "https://github.com",
    "yandex": "https://yandex.ru",
    "яндекс": "https://yandex.ru",
}

# Маппинг названий на домены (главное!)
SITE_DOMAINS: Dict[str, List[str]] = {
    "вк": ["vk.com", "vk.ru"],
    "vk": ["vk.com", "vk.ru"],
    "вконтакте": ["vk.com", "vk.ru"],
    
    "ютуб": ["youtube.com", "youtu.be"],
    "youtube": ["youtube.com", "youtu.be"],
    
    "гугл": ["google.com", "google.ru"],
    "google": ["google.com", "google.ru"],
    
    "яндекс": ["yandex.ru", "yandex.com", "ya.ru"],
    "yandex": ["yandex.ru", "yandex.com", "ya.ru"],
    
    "телеграм": ["telegram.org", "t.me", "web.telegram.org"],
    "telegram": ["telegram.org", "t.me", "web.telegram.org"],
    
    "гитхаб": ["github.com"],
    "github": ["github.com"],
    
    "твиттер": ["twitter.com", "x.com"],
    "twitter": ["twitter.com", "x.com"],
    
    "инстаграм": ["instagram.com"],
    "instagram": ["instagram.com"],
    
    "дискорд": ["discord.com", "discord.gg"],
    "discord": ["discord.com", "discord.gg"],
    
    "реддит": ["reddit.com"],
    "reddit": ["reddit.com"],
    
    "тикток": ["tiktok.com"],
    "tiktok": ["tiktok.com"],
    
    "твич": ["twitch.tv"],
    "twitch": ["twitch.tv"],
    
    "mail": ["mail.ru"],
    "мейл": ["mail.ru"],
    "почта": ["mail.ru", "gmail.com"],
    
    "gmail": ["gmail.com", "mail.google.com"],
    "гмейл": ["gmail.com", "mail.google.com"],
    
    "whatsapp": ["web.whatsapp.com", "whatsapp.com"],
    "ватсап": ["web.whatsapp.com", "whatsapp.com"],
    
    "одноклассники": ["ok.ru"],
    "ок": ["ok.ru"],
    
    "авито": ["avito.ru"],
    "avito": ["avito.ru"],
    
    "озон": ["ozon.ru"],
    "ozon": ["ozon.ru"],
    
    "wildberries": ["wildberries.ru"],
    "вайлдберриз": ["wildberries.ru"],
    "wb": ["wildberries.ru"],
    
    "chatgpt": ["chat.openai.com", "chatgpt.com"],
    "чатгпт": ["chat.openai.com", "chatgpt.com"],
    
    "claude": ["claude.ai"],
    "клод": ["claude.ai"],
}

# Алиасы процессов
PROCESS_ALIASES: Dict[str, List[str]] = {
    "chrome": ["chrome.exe"],
    "firefox": ["firefox.exe"],
    "telegram": ["telegram.exe"],
    "discord": ["discord.exe", "Discord.exe"],
    "vscode": ["Code.exe", "code.exe"],
    "word": ["WINWORD.EXE", "winword.exe"],
    "excel": ["EXCEL.EXE", "excel.exe"],
}


def get_browser_url_from_window(hwnd) -> Optional[str]:
    """
    Получить URL из адресной строки браузера через UI Automation
    """
    try:
        import uiautomation as auto
        
        # Получаем контрол окна
        control = auto.ControlFromHandle(hwnd)
        if not control:
            return None
        
        # Ищем адресную строку (Edit control с URL)
        # Разные браузеры имеют разную структуру, пробуем несколько способов
        
        # Способ 1: Искать Edit control
        edit = control.EditControl(searchDepth=8)
        if edit and edit.Exists(0.1):
            url = edit.GetValuePattern().Value if edit.GetValuePattern() else ""
            if url and ('http' in url or '.' in url):
                return url
        
        # Способ 2: Через Name содержащий URL
        for ctrl in control.GetChildren():
            name = ctrl.Name or ""
            if 'http' in name.lower() or '.com' in name.lower() or '.ru' in name.lower():
                return name
                
    except ImportError:
        return None
    except Exception:
        return None
    
    return None


def find_browser_tabs_with_domain(target_domains: List[str]) -> List[Tuple[int, str, str]]:
    """
    Найти вкладки браузера, содержащие указанные домены
    Возвращает: [(hwnd, title, найденный_домен), ...]
    """
    if sys.platform != "win32":
        return []
    
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError:
        return []
    
    results = []
    browser_processes = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'browser.exe', 
                         'opera.exe', 'brave.exe', 'yandex.exe', 'iexplore.exe']
    
    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
        
        # Проверяем, это окно браузера?
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            proc_name = process.name().lower()
            
            is_browser = any(bp in proc_name for bp in browser_processes)
            if not is_browser:
                return True
        except:
            # Если не можем определить процесс, проверяем по заголовку
            browser_markers = ['Chrome', 'Firefox', 'Edge', 'Opera', 'Brave', 'Браузер', 'Browser']
            if not any(marker.lower() in title.lower() for marker in browser_markers):
                return True
        
        # Пробуем получить URL из адресной строки
        url = get_browser_url_from_window(hwnd)
        
        title_lower = title.lower()
        
        # Проверяем домены
        for domain in target_domains:
            domain_lower = domain.lower()
            
            # Проверяем URL если получили
            if url and domain_lower in url.lower():
                results.append((hwnd, title, domain))
                return True
            
            # Проверяем заголовок (fallback)
            if domain_lower in title_lower:
                results.append((hwnd, title, domain))
                return True
        
        return True
    
    try:
        win32gui.EnumWindows(callback, None)
    except:
        pass
    
    return results


def close_browser_tab_by_domain(site_name: str) -> str:
    """
    Закрыть вкладку браузера по названию сайта (ищем по домену)
    """
    if sys.platform != "win32":
        return "Закрытие вкладок работает только на Windows"
    
    try:
        import pyautogui
        import win32gui
        import win32con
    except ImportError as e:
        return f"Не хватает библиотеки: {e}"
    
    site_lower = site_name.lower().strip()
    
    # Получаем домены для этого сайта
    domains = SITE_DOMAINS.get(site_lower)
    
    if not domains:
        # Если сайт неизвестен, используем само название как домен
        domains = [site_lower, f"{site_lower}.com", f"{site_lower}.ru"]
    
    # Ищем вкладки с этими доменами
    found_tabs = find_browser_tabs_with_domain(domains)
    
    if not found_tabs:
        return f"Не нашла открытую вкладку {site_name}"
    
    # Берём первую найденную
    hwnd, title, domain = found_tabs[0]
    
    try:
        # Восстанавливаем окно если свёрнуто
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.15)
        
        # Активируем окно
        try:
            win32gui.SetForegroundWindow(hwnd)
        except:
            # Альтернативный способ через ctypes
            import ctypes
            ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        
        time.sleep(0.2)
        
        # Закрываем вкладку
        pyautogui.hotkey('ctrl', 'w')
        
        return f"Закрыла вкладку {site_name}!"
        
    except Exception as e:
        return f"Ошибка при закрытии: {e}"


def close_browser_tab(site_name: str) -> str:
    """Обёртка для совместимости"""
    return close_browser_tab_by_domain(site_name)


def open_site(url: str, name: str = "") -> str:
    """Открыть сайт"""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        
        webbrowser.open(url)
        
        if name:
            return f"Открываю {name}"
        return f"Открываю сайт"
        
    except Exception as e:
        return f"Не могу открыть сайт: {e}"


def open_program(name_or_path: str, display_name: str = "") -> str:
    """Открыть программу"""
    
    name_lower = name_or_path.lower().strip()
    
    if name_lower in KNOWN_PROGRAMS:
        program = KNOWN_PROGRAMS[name_lower]
    else:
        program = name_or_path
    
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                program,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                [program],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        return f"Открываю {display_name or name_lower}"
        
    except Exception as e:
        return f"Ошибка запуска: {e}"


def close_program(name: str) -> str:
    """Закрыть программу"""
    
    name_lower = name.lower().strip()
    
    # Сначала проверяем — это сайт? Тогда закрываем вкладку
    if name_lower in SITE_DOMAINS:
        return close_browser_tab_by_domain(name_lower)
    
    # Проверяем, похоже ли на домен (содержит точку)
    if '.' in name_lower:
        return close_browser_tab_by_domain(name_lower)
    
    # Получаем возможные имена процессов
    process_names = []
    
    if name_lower in PROCESS_ALIASES:
        process_names = PROCESS_ALIASES[name_lower]
    else:
        process_names = [f"{name_lower}.exe", name_lower]
    
    try:
        if sys.platform == "win32":
            killed = False
            for proc_name in process_names:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    killed = True
                    break
            
            if killed:
                return f"Закрыла {name}"
            else:
                # Может это сайт который мы не знаем?
                # Пробуем закрыть как вкладку
                result = close_browser_tab_by_domain(name_lower)
                if "Закрыла" in result:
                    return result
                return f"Не нашла {name}"
        else:
            for proc_name in process_names:
                subprocess.run(["pkill", "-f", proc_name], capture_output=True)
            return f"Закрыла {name}"
            
    except Exception as e:
        return f"Ошибка закрытия: {e}"


def search_web(query: str) -> str:
    """Поиск в интернете"""
    try:
        import urllib.parse
        search_url = SEARCH_ENGINE + urllib.parse.quote(query)
        webbrowser.open(search_url)
        return f"Ищу '{query}'"
    except Exception as e:
        return f"Ошибка поиска: {e}"


def set_volume(level) -> str:
    """Установить громкость"""
    
    try:
        if sys.platform != "win32":
            return "Управление громкостью только на Windows"
        
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        current = volume.GetMasterVolumeLevelScalar()
        
        if isinstance(level, str):
            if level.startswith("+"):
                delta = int(level[1:]) / 100
                new_level = min(1.0, current + delta)
            elif level.startswith("-"):
                delta = int(level[1:]) / 100
                new_level = max(0.0, current - delta)
            else:
                new_level = int(level) / 100
        else:
            new_level = int(level) / 100
        
        new_level = max(0.0, min(1.0, new_level))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        
        return f"Громкость: {int(new_level * 100)}%"
        
    except ImportError:
        return "Установи pycaw: pip install pycaw"
    except Exception as e:
        return f"Ошибка громкости: {e}"


def get_volume() -> int:
    """Получить текущую громкость"""
    
    try:
        if sys.platform != "win32":
            return 50
        
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        return int(volume.GetMasterVolumeLevelScalar() * 100)
        
    except:
        return 50


def take_screenshot(name: str = None) -> str:
    """Сделать скриншот"""
    
    try:
        from PIL import ImageGrab
        from datetime import datetime
        
        os.makedirs(SCREENSHOT_PATH, exist_ok=True)
        
        if not name:
            name = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        elif not name.endswith(".png"):
            name += ".png"
        
        filepath = os.path.join(SCREENSHOT_PATH, name)
        
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        
        return f"Скриншот сохранён: {filepath}"
        
    except ImportError:
        return "Установи Pillow: pip install Pillow"
    except Exception as e:
        return f"Ошибка скриншота: {e}"


def get_system_info() -> Dict:
    """Информация о системе"""
    
    import platform
    
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
    }
    
    try:
        import psutil
        info["cpu_percent"] = psutil.cpu_percent()
        info["memory_percent"] = psutil.virtual_memory().percent
        info["disk_percent"] = psutil.disk_usage('/').percent
    except:
        pass
    
    return info


# === ТЕСТ ===
if __name__ == "__main__":
    print("🖥️ Тест управления ПК v3.0")
    print(f"Громкость: {get_volume()}%")
    print(f"Система: {get_system_info()}")
    print()
    print("Известные сайты для закрытия:")
    for site in list(SITE_DOMAINS.keys())[:10]:
        print(f"  - {site}: {SITE_DOMAINS[site]}")
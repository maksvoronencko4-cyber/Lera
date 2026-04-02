"""
🧠 МОЗГ ЛЕРЫ v5.5.0 — УМНЫЕ ДЕЙСТВИЯ ЧЕРЕЗ AI
Логика: Пользователь → Лера → AI → Лера → Пользователь
"""
import os
import sys
import json
import time
import random
import re
import webbrowser
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === НАСТРОЙКИ ===
try:
    from config import CONTEXT_SIZE, MAX_TOKENS, TEMPERATURE, N_THREADS, N_BATCH
except:
    CONTEXT_SIZE = 512
    MAX_TOKENS = 100
    TEMPERATURE = 0.7
    N_THREADS = 4
    N_BATCH = 64

# === ИМПОРТЫ МОДУЛЕЙ ===
try:
    from core.ai_providers import get_ai_manager, AIManager
    HAS_AI_MANAGER = True
except ImportError:
    HAS_AI_MANAGER = False
    print("⚠️ AI Manager недоступен")

try:
    from core.malware_scanner import scan_and_report
    HAS_SCANNER = True
except:
    HAS_SCANNER = False

try:
    from core.learning import lera_learning
    HAS_LEARNING = True
except:
    HAS_LEARNING = False

try:
    from core.emotion_detector import detect_emotion
    HAS_EMOTIONS = True
except:
    HAS_EMOTIONS = False

try:
    import psutil
    HAS_PSUTIL = True
except:
    HAS_PSUTIL = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.03
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


# ============================================================
# ПАМЯТЬ
# ============================================================

class LeraMemory:
    def __init__(self, path: str = "data/lera_memory.json"):
        self.path = path
        self.learned_apps = {}
        self.learned_sites = {}
        self.knowledge_cache = {}
        self.conversation_history = []
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_apps = data.get("learned_apps", {})
                    self.learned_sites = data.get("learned_sites", {})
                    self.knowledge_cache = data.get("knowledge_cache", {})
                    return data
            except:
                pass
        return {
            "user_name": "",
            "last_talked": None,
            "facts": [],
            "learned_apps": {},
            "learned_sites": {},
            "knowledge_cache": {}
        }

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.data["learned_apps"] = self.learned_apps
        self.data["learned_sites"] = self.learned_sites
        self.data["knowledge_cache"] = self.knowledge_cache
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_user_name(self) -> str:
        return self.data.get("user_name", "")

    def set_user_name(self, name: str):
        self.data["user_name"] = name
        self.save()

    def learn_app(self, name: str, path: str):
        self.learned_apps[name.lower()] = path
        self.save()

    def learn_site(self, name: str, url: str):
        self.learned_sites[name.lower()] = url
        self.save()

    def get_app(self, name: str) -> Optional[str]:
        return self.learned_apps.get(name.lower())

    def get_site(self, name: str) -> Optional[str]:
        return self.learned_sites.get(name.lower())

    def learn_knowledge(self, name: str, info: dict):
        self.knowledge_cache[name.lower()] = info
        self.save()

    def get_knowledge(self, name: str) -> Optional[dict]:
        return self.knowledge_cache.get(name.lower())

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def get_context(self, last_n: int = 6) -> list:
        return self.conversation_history[-last_n:]


# ============================================================
# СИСТЕМНЫЕ КОМАНДЫ
# ============================================================

SYSTEM_COMMANDS = {
    "время": lambda: f"Сейчас {datetime.now().strftime('%H:%M')}",
    "который час": lambda: f"Сейчас {datetime.now().strftime('%H:%M')}",
    "сколько времени": lambda: f"Сейчас {datetime.now().strftime('%H:%M')}",
    "дата": lambda: f"Сегодня {datetime.now().strftime('%d.%m.%Y')}",
    "какое число": lambda: f"Сегодня {datetime.now().strftime('%d.%m.%Y')}",
    "какая дата": lambda: f"Сегодня {datetime.now().strftime('%d.%m.%Y')}",
}


# ============================================================
# МОЗГ ЛЕРЫ v5.5
# ============================================================

class LeraBrain:
    def __init__(self):
        self.memory = LeraMemory()
        self.ai_manager: Optional[AIManager] = None
        self.is_ready = False
        self.model_loaded = False

        self.personality = """Ты Лера — девушка 22 лет, весёлая и дружелюбная помощница.
Ты НЕ робот, ты живой человек. Общаешься естественно и непринуждённо.
Используешь разговорный стиль: "ну", "типа", "короче", "хах", "кстати".
Отвечаешь коротко — 1-2 предложения, если не просят подробнее.
Можешь шутить, иронизировать, проявлять эмоции.
Если не знаешь что-то — честно говоришь, не выдумываешь.
Помогаешь с компьютером: открываешь сайты, программы, ищешь информацию."""

        self._init_ai()

    def _init_ai(self):
        if HAS_AI_MANAGER:
            try:
                self.ai_manager = get_ai_manager()
                providers = self.ai_manager.get_available_providers()
                if providers:
                    print(f"✅ AI провайдеры: {', '.join(providers)}")
                    self.is_ready = True
                    self.model_loaded = True
                else:
                    print("⚠️ Нет доступных AI провайдеров")
            except Exception as e:
                print(f"⚠️ Ошибка AI Manager: {e}")

        if not self.is_ready:
            print("⚠️ AI недоступен, работаю в ограниченном режиме")
            self.is_ready = True

    def load_model(self):
        if not self.is_ready:
            self._init_ai()
        self.model_loaded = True
        return True

    def get_status(self) -> dict:
        providers = []
        if self.ai_manager:
            providers = self.ai_manager.get_available_providers()
        return {
            "ready": self.is_ready,
            "model_loaded": self.model_loaded,
            "ai_providers": providers,
            "user_name": self.memory.get_user_name()
        }

    # ============================================================
    # ОБРАБОТКА ТЕКСТА
    # ============================================================

    def _clean_text(self, text: str) -> str:
        text = text.strip()
        text_lower = text.lower()
        for prefix in ["лера ", "лера, ", "лер ", "лер, ", "эй лера ", "эй лера, "]:
            if text_lower.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        return text

    def _is_system_command(self, text: str) -> Optional[str]:
        text_lower = text.lower().strip()
        for cmd, func in SYSTEM_COMMANDS.items():
            if text_lower == cmd or text_lower.endswith(cmd):
                return func()
        return None

    def _is_wake_word(self, text: str) -> bool:
        return text.lower().strip() in ["лера", "лер", "эй лера"]

    def _detect_intent(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()

        # Открыть
        if any(w in text_lower for w in ["открой", "запусти", "включи", "открыть", "зайди"]):
            target = ""
            for prefix in ["открой ", "запусти ", "включи ", "открыть ", "зайди на ", "зайди в "]:
                if prefix in text_lower:
                    target = text_lower.split(prefix, 1)[1].strip()
                    break
            if target:
                return {"intent": "open", "target": target, "confidence": 0.9}

        # Поиск
        if any(w in text_lower for w in ["найди", "поищи", "загугли", "найти"]):
            target = ""
            for prefix in ["найди ", "поищи ", "загугли ", "найти "]:
                if prefix in text_lower:
                    target = text_lower.split(prefix, 1)[1].strip()
                    break
            if target:
                return {"intent": "search", "target": target, "confidence": 0.9}

        # Громкость
        if any(w in text_lower for w in ["громкость", "громче", "тише", "звук"]):
            return {"intent": "volume", "target": text, "confidence": 0.9}

        # Скриншот
        if any(w in text_lower for w in ["скриншот", "снимок экрана"]):
            return {"intent": "screenshot", "target": "", "confidence": 0.9}

        # Сканирование
        if any(w in text_lower for w in ["сканируй", "проверь на вирус", "антивирус"]):
            return {"intent": "scan", "target": "", "confidence": 0.9}

        return {"intent": "chat", "target": text, "confidence": 0.7}

    def _ask_ai_what_is(self, target: str, action: str = "открыть") -> Dict[str, Any]:
        target_lower = target.lower().strip()

        # 1. Кэш знаний
        cached = self.memory.get_knowledge(target)
        if cached:
            print(f"💾 Из памяти: {target} → {cached.get('type')} ({cached.get('domain') or cached.get('process', '?')})")
            return cached

        # 2. Старая память
        remembered_site = self.memory.get_site(target)
        if remembered_site and not remembered_site.endswith('.exe'):
            domain = remembered_site.replace("https://", "").replace("http://", "").rstrip("/")
            info = {
                "type": "site",
                "domain": domain,
                "url": remembered_site,
                "name": target
            }
            self.memory.learn_knowledge(target, info)
            print(f"💾 Из старой памяти: {target} = {remembered_site}")
            return info

        remembered_app = self.memory.get_app(target)
        if remembered_app:
            info = {
                "type": "app",
                "process": remembered_app,
                "name": target
            }
            self.memory.learn_knowledge(target, info)
            print(f"💾 Из старой памяти: {target} = {remembered_app}")
            return info

        # 3. Спрашиваем AI
        if not self.ai_manager:
            return {"type": "unknown", "name": target}

        print(f"🤔 Спрашиваю AI: что такое '{target}'...")

        prompt = f"""Пользователь хочет {action}: "{target}"

Определи что это и ответь СТРОГО в формате JSON (без markdown, без ```, без пояснений):
{{
    "type": "site" или "program",
    "domain": "домен сайта, например vk.com",
    "process": "имя процесса Windows, например telegram.exe",
    "name": "полное название"
}}

Ответь ТОЛЬКО JSON:"""

        response = self.ai_manager.chat(prompt, "Отвечай ТОЛЬКО валидным JSON. Без markdown.")

        if response:
            info = self._parse_ai_json(response, target)
            if info and info["type"] != "unknown":
                self.memory.learn_knowledge(target, info)

                if info["type"] == "site" and info.get("domain"):
                    url = f"https://{info['domain']}"
                    info["url"] = url
                    self.memory.learn_site(target, url)
                elif info["type"] in ["app", "program"] and info.get("process"):
                    info["type"] = "app"
                    self.memory.learn_app(target, info["process"])

                print(f"🧠 AI: {target} → {info['type']} | {info.get('domain') or info.get('process')}")
                return info

        print(f"🎲 AI не помог, угадываю...")
        guessed = self._guess_target(target_lower)
        self.memory.learn_knowledge(target, guessed)
        return guessed

    def _parse_ai_json(self, response: str, target: str) -> Optional[Dict]:
        try:
            response = response.strip()
            response = re.sub(r'^```json?\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
            response = response.strip()

            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group())

                if "type" not in info:
                    info["type"] = "unknown"

                if info["type"] in ["program", "app", "application", "программа"]:
                    info["type"] = "app"
                elif info["type"] in ["site", "website", "web", "сайт"]:
                    info["type"] = "site"

                return info

        except Exception as e:
            print(f"⚠️ Ошибка парсинга: {e}")

        return {"type": "unknown", "name": target}

    def _guess_target(self, target: str) -> Dict:
        if any(c in target for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"):
            domain = f"{target.replace(' ', '')}.ru"
        else:
            domain = f"{target.replace(' ', '')}.com"

        return {
            "type": "site",
            "domain": domain,
            "url": f"https://{domain}",
            "name": target
        }

    # ============================================================
    # 🚀 УМНОЕ ОТКРЫТИЕ
    # ============================================================

    def _smart_open(self, target: str) -> str:
        info = self._ask_ai_what_is(target, "открыть")

        if info["type"] == "site":
            domain = info.get("domain", "")
            url = info.get("url", "")

            if not url and domain:
                url = f"https://{domain}"
            elif not url:
                url = f"https://{target.replace(' ', '')}.com"

            print(f"🌐 Открываю: {url}")
            webbrowser.open(url)
            return f"Открываю {info.get('name', target)}!"

        elif info["type"] == "app":
            process = info.get("process", "")

            if not process:
                return f"Не знаю как запустить {target}"

            if HAS_PSUTIL:
                proc_name = process.replace('.exe', '').lower()
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc_name in proc.info['name'].lower():
                            return f"{info.get('name', target)} уже запущен!"
                    except:
                        continue

            program = process.replace(".exe", "")
            print(f"💻 Запускаю: {program}")

            try:
                subprocess.Popen(program, shell=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                return f"Запускаю {info.get('name', target)}!"
            except Exception as e:
                return f"Не смогла запустить {target}: {e}"

        else:
            import urllib.parse
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(target)}")
            return f"Не знаю что такое {target}, ищу в Google!"

    # ============================================================
    # 🎬 ВЫПОЛНЕНИЕ ДЕЙСТВИЙ
    # ============================================================

    def _execute_intent(self, intent: str, target: str, original_text: str) -> Optional[str]:

        if intent == "open":
            return self._smart_open(target)

        if intent == "search":
            import urllib.parse
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(target)}")
            return f"Ищу '{target}' в Google!"

        if intent == "volume":
            try:
                from core.pc_control import set_volume, get_volume
                numbers = re.findall(r'\d+', original_text)
                if numbers:
                    return set_volume(int(numbers[0]))
                elif "громче" in original_text.lower():
                    return set_volume("+10")
                elif "тише" in original_text.lower():
                    return set_volume("-10")
                return f"Громкость: {get_volume()}%"
            except Exception as e:
                return f"Ошибка громкости: {e}"

        if intent == "screenshot":
            try:
                from core.pc_control import take_screenshot
                return take_screenshot()
            except Exception as e:
                return f"Ошибка скриншота: {e}"

        if intent == "scan":
            if HAS_SCANNER:
                return scan_and_report()
            return "Сканер недоступен"

        return None

    # ============================================================
    # 💬 ГЕНЕРАЦИЯ ОТВЕТА
    # ============================================================

    def _generate_chat_response(self, text: str) -> str:
        if not self.ai_manager:
            return self._simple_response(text)

        context = self.memory.get_context(6)
        user_name = self.memory.get_user_name()

        emotion = None
        if HAS_EMOTIONS:
            try:
                emotion = detect_emotion(text)
            except:
                pass

        system = self.personality
        if user_name:
            system += f"\nСобеседника зовут {user_name}."
        if emotion:
            system += f"\nЭмоция пользователя: {emotion}."

        messages_context = ""
        if context:
            for msg in context:
                role = "Пользователь" if msg["role"] == "user" else "Лера"
                messages_context += f"{role}: {msg['content']}\n"

        full_prompt = text
        if messages_context:
            full_prompt = f"История:\n{messages_context}\nПользователь: {text}"

        response = self.ai_manager.chat(full_prompt, system)

        if response:
            response = self._clean_response(response)
            self.memory.add_to_history("user", text)
            self.memory.add_to_history("assistant", response)
            return response

        return self._simple_response(text)

    def _clean_response(self, text: str) -> str:
        text = re.sub(r'[\*\_\#\`]', '', text)
        for prefix in ["лера:", "assistant:", "Лера:", "AI:", "Ассистент:"]:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _simple_response(self, text: str) -> str:
        text_lower = text.lower()

        if any(w in text_lower for w in ["привет", "здравствуй", "хай"]):
            return random.choice(["Привет!", "Хей!", "Приветик!"])

        if any(w in text_lower for w in ["как дела", "как ты"]):
            return random.choice(["Отлично! А ты как?", "Норм! Чем займёмся?"])

        if any(w in text_lower for w in ["спасибо", "спс"]):
            return random.choice(["Не за что!", "Обращайся!"])

        if any(w in text_lower for w in ["пока", "до свидания"]):
            return random.choice(["Пока!", "До встречи!"])

        if any(w in text_lower for w in ["кто ты", "ты кто"]):
            return "Я Лера — твоя виртуальная помощница!"

        return random.choice(["Интересно! Расскажи подробнее?", "Хм, понятно!"])

    # ============================================================
    # 🧠 ГЛАВНАЯ ФУНКЦИЯ
    # ============================================================

    def think(self, user_message: str) -> Optional[str]:
        if not user_message or not user_message.strip():
            return None

        user_message = user_message.strip()
        cleaned_text = self._clean_text(user_message)

        print(f"💭 '{user_message}'")

        # 1. Позвали Леру
        if self._is_wake_word(user_message):
            name = self.memory.get_user_name()
            responses = ["Да?", "Слушаю!", "Что?", "Тут!"]
            if name:
                responses.extend([f"Да, {name}?"])
            return random.choice(responses)

        # 2. Системные команды
        system_response = self._is_system_command(cleaned_text)
        if system_response:
            return system_response

        # 3. Определяем намерение
        intent_data = self._detect_intent(cleaned_text)
        intent = intent_data["intent"]
        target = intent_data["target"]

        print(f"🎯 Intent: {intent}, Target: {target}")

        # 4. Выполняем действие
        if intent != "chat":
            result = self._execute_intent(intent, target, cleaned_text)
            if result:
                return result

        # 5. Чат
        return self._generate_chat_response(cleaned_text)


# ============================================================
# ГЛОБАЛЬНЫЕ ФУНКЦИИ
# ============================================================

_brain = None


def get_brain() -> LeraBrain:
    global _brain
    if _brain is None:
        _brain = LeraBrain()
    return _brain


def load_model():
    return get_brain().load_model()


def think(user_message, **kwargs) -> str:
    brain = get_brain()
    if isinstance(user_message, dict):
        user_message = user_message.get("text", "")
    return brain.think(user_message)


def get_status() -> dict:
    return get_brain().get_status()


def is_ready() -> bool:
    return get_brain().is_ready
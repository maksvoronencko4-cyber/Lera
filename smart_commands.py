"""
УМНЫЕ КОМАНДЫ ЧЕРЕЗ AI - OpenRouter API
"""
import re
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

AI_MODEL = "arcee-ai/trinity-large-preview:free"

KNOWN_APPS = {
    "блокнот": "notepad",
    "калькулятор": "calc",
    "проводник": "explorer",
    "paint": "mspaint",
    "пейнт": "mspaint",
    "терминал": "cmd",
    "браузер": "chrome",
    "хром": "chrome",
    "chrome": "chrome",
    "edge": "msedge",
    "firefox": "firefox",
    "word": "winword",
    "ворд": "winword",
    "excel": "excel",
    "vscode": "code",
    "телеграм": "telegram",
    "дискорд": "discord",
    "стим": "steam",
    "steam": "steam",
}

KNOWN_SITES = {
    # === ПОИСКОВИКИ ===
    "ютуб": "youtube.com",
    "youtube": "youtube.com",
    "гугл": "google.com",
    "google": "google.com",
    "яндекс": "ya.ru",
    "yandex": "ya.ru",
    "дзен": "dzen.ru",
    "бинг": "bing.com",
    "bing": "bing.com",

    # === СОЦСЕТИ ===
    "вк": "vk.com",
    "вконтакте": "vk.com",
    "контакт": "vk.com",
    "инстаграм": "instagram.com",
    "инста": "instagram.com",
    "instagram": "instagram.com",
    "твиттер": "twitter.com",
    "twitter": "twitter.com",
    "x": "x.com",
    "тикток": "tiktok.com",
    "tiktok": "tiktok.com",
    "фейсбук": "facebook.com",
    "facebook": "facebook.com",
    "одноклассники": "ok.ru",
    "ок": "ok.ru",
    "телеграм веб": "web.telegram.org",
    "telegram": "web.telegram.org",
    "снэпчат": "snapchat.com",
    "snapchat": "snapchat.com",
    "пинтерест": "pinterest.com",
    "pinterest": "pinterest.com",
    "линкедин": "linkedin.com",
    "linkedin": "linkedin.com",

    # === СТРИМИНГ/ВИДЕО ===
    "твич": "twitch.tv",
    "twitch": "twitch.tv",
    "нетфликс": "netflix.com",
    "netflix": "netflix.com",
    "кинопоиск": "kinopoisk.ru",
    "rutube": "rutube.ru",
    "рутуб": "rutube.ru",
    "иви": "ivi.ru",
    "ivi": "ivi.ru",
    "окко": "okko.tv",
    "okko": "okko.tv",

    # === РАЗРАБОТКА ===
    "гитхаб": "github.com",
    "github": "github.com",
    "гитлаб": "gitlab.com",
    "gitlab": "gitlab.com",
    "stackoverflow": "stackoverflow.com",
    "стэковерфлоу": "stackoverflow.com",
    "codepen": "codepen.io",

    # === ПОЧТА ===
    "почта": "mail.google.com",
    "gmail": "mail.google.com",
    "гмейл": "mail.google.com",
    "mail": "mail.ru",
    "мейл": "mail.ru",
    "яндекс почта": "mail.yandex.ru",
    "outlook": "outlook.com",

    # === МЕССЕНДЖЕРЫ ===
    "дискорд": "discord.com",
    "discord": "discord.com",
    "ватсап": "web.whatsapp.com",
    "whatsapp": "web.whatsapp.com",
    "зум": "zoom.us",
    "zoom": "zoom.us",
    "slack": "slack.com",

    # === ИГРЫ ===
    "стим": "store.steampowered.com",
    "steam": "store.steampowered.com",
    "эпик": "epicgames.com",
    "epic": "epicgames.com",
    "роблокс": "roblox.com",
    "roblox": "roblox.com",

    # === МАРКЕТПЛЕЙСЫ ===
    "озон": "ozon.ru",
    "ozon": "ozon.ru",
    "вайлдберриз": "wildberries.ru",
    "wildberries": "wildberries.ru",
    "вб": "wildberries.ru",
    "алиэкспресс": "aliexpress.ru",
    "aliexpress": "aliexpress.ru",
    "али": "aliexpress.ru",
    "авито": "avito.ru",
    "avito": "avito.ru",
    "амазон": "amazon.com",
    "amazon": "amazon.com",
    "ситилинк": "citilink.ru",
    "днс": "dns-shop.ru",
    "dns": "dns-shop.ru",
    "мвидео": "mvideo.ru",
    "mvideo": "mvideo.ru",

    # === МУЗЫКА ===
    "спотифай": "spotify.com",
    "spotify": "spotify.com",
    "яндекс музыка": "music.yandex.ru",
    "soundcloud": "soundcloud.com",

    # === НОВОСТИ/ФОРУМЫ ===
    "хабр": "habr.com",
    "habr": "habr.com",
    "пикабу": "pikabu.ru",
    "pikabu": "pikabu.ru",
    "реддит": "reddit.com",
    "reddit": "reddit.com",

    # === ПЕРЕВОДЧИКИ ===
    "переводчик": "translate.google.com",
    "гугл переводчик": "translate.google.com",
    "deepl": "deepl.com",

    # === КАРТЫ ===
    "карты": "maps.google.com",
    "гугл карты": "maps.google.com",
    "яндекс карты": "maps.yandex.ru",
    "2гис": "2gis.ru",

    # === БАНКИ/ФИНАНСЫ ===
    "сбербанк": "online.sberbank.ru",
    "сбер": "online.sberbank.ru",
    "тинькофф": "tinkoff.ru",
    "tinkoff": "tinkoff.ru",
    "госуслуги": "gosuslugi.ru",
    "налог ру": "nalog.ru",
    "binance": "binance.com",
    "бинанс": "binance.com",

    # === ДИЗАЙН ===
    "figma": "figma.com",
    "фигма": "figma.com",
    "canva": "canva.com",
    "канва": "canva.com",

    # === AI ===
    "chatgpt": "chat.openai.com",
    "чатгпт": "chat.openai.com",
    "claude": "claude.ai",
    "клод": "claude.ai",
    "midjourney": "midjourney.com",
    "gigachat": "gigachat.ru",
    "гигачат": "gigachat.ru",
    "perplexity": "perplexity.ai",
    "copilot": "copilot.microsoft.com",
    "gemini": "gemini.google.com",

    # === ФАЙЛЫ/ОБЛАКА ===
    "гугл диск": "drive.google.com",
    "яндекс диск": "disk.yandex.ru",
    "dropbox": "dropbox.com",
    "облако mail": "cloud.mail.ru",

    # === ОБРАЗОВАНИЕ ===
    "википедия": "wikipedia.org",
    "вики": "wikipedia.org",
    "wikipedia": "wikipedia.org",

    # === РАБОТА ===
    "hh": "hh.ru",
    "хедхантер": "hh.ru",
    "headhunter": "hh.ru",
    "госуслуги": "gosuslugi.ru",

    # === 18+ ===
    "pornhub": "pornhub.com",
    "порнхаб": "pornhub.com",
    "xvideos": "xvideos.com",
    "xhamster": "xhamster.com",
    "onlyfans": "onlyfans.com",
    "онлифанс": "onlyfans.com",
    "chaturbate": "chaturbate.com",
    "bongacams": "bongacams.com",
    "stripchat": "stripchat.com",
    "hentai": "hanime.tv",
    "хентай": "hanime.tv",
    "nhentai": "nhentai.net",
    "rule34": "rule34.xxx",
    "рул34": "rule34.xxx",
    "порно": "pornhub.com",
}


def is_command_message(text: str) -> bool:
    """Быстрая проверка — похоже ли на команду"""
    text_lower = text.lower()
    command_words = [
        "открой", "запусти", "включи", "закрой", "выключи",
        "найди", "поищи", "загугли", "погугли",
        "громкость", "громче", "тише", "звук",
        "скриншот", "снимок",
        "выключи компьютер", "перезагрузи", "заблокируй",
        "напиши", "напечатай",
        "создай папку", "удали файл",
    ]
    return any(word in text_lower for word in command_words)


def parse_command_with_ai(user_message: str):
    """Использует ИИ чтобы понять команду"""
    if not is_command_message(user_message):
        return None

    prompt = f"""Определи команду из сообщения. Верни ТОЛЬКО JSON.

Сообщение: "{user_message}"

Формат: {{"action": "тип", "target": "цель"}}

Действия для ГРОМКОСТИ:
- "volume_set" — установить громкость НА конкретный уровень (пример: "громкость на 50%", "громкость 2 процента", "поставь громкость 30")
- "volume_up" — сделать громче (пример: "громче", "прибавь звук", "громче на 10")
- "volume_down" — сделать тише (пример: "тише", "убавь звук", "тише на 20")
- "mute" — выключить звук
- "unmute" — включить звук

ВАЖНО для громкости:
- "громкость на 2%" или "громкость 2 процента" → volume_set с target "2"
- "громче на 10%" → volume_up с target "10"
- "громче" без числа → volume_up с target "10"
- "тише" без числа → volume_down с target "10"

Другие действия:
- "open_app" — открыть приложение
- "close_app" — закрыть приложение
- "open_site" — открыть сайт
- "search_google" — поиск в гугле
- "search_youtube" — поиск на ютубе
- "screenshot" — скриншот
- "shutdown" — выключить пк
- "restart" — перезагрузить
- "lock" — заблокировать
- "none" — НЕ команда

Примеры:
"громкость на 50" → {{"action": "volume_set", "target": "50"}}
"громкость 2 процента" → {{"action": "volume_set", "target": "2"}}
"сделай громче" → {{"action": "volume_up", "target": "10"}}
"тише" → {{"action": "volume_down", "target": "10"}}
"открой ютуб" → {{"action": "open_site", "target": "youtube.com"}}
"запусти блокнот" → {{"action": "open_app", "target": "блокнот"}}
"найди котиков" → {{"action": "search_google", "target": "котиков"}}
"как дела" → {{"action": "none", "target": ""}}

ВАЖНО: Если это обычный разговор или вопрос — верни {{"action": "none", "target": ""}}

JSON:"""

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.1,
        )

        answer     = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[^}]+\}', answer)

        if json_match:
            result = json.loads(json_match.group())

            if result.get("action") == "none":
                return None

            action = result.get("action", "")
            target = result.get("target", "").lower().strip()

            # Убираем слово "процент" из target
            target = target.replace("процент", "").replace("%", "").strip()
            result["target"] = target

            if action == "open_app" and target in KNOWN_APPS:
                result["target"] = KNOWN_APPS[target]

            if action == "open_site" and target in KNOWN_SITES:
                result["target"] = KNOWN_SITES[target]

            return result

    except Exception as e:
        print(f"⚠️ smart_commands AI: {e}")

    return None


def execute_smart_command(command: dict):
    """Выполняет команду"""
    from core.pc_control import execute_command

    if not command:
        return None

    action = command.get("action", "")
    target = command.get("target", "")

    action_map = {
        "open_app":      "open_app",
        "close_app":     "close_app",
        "open_site":     "website",
        "search_google": "search",
        "search_youtube":"youtube",
        "volume_up":     "volume_up",
        "volume_down":   "volume_down",
        "volume_set":    "volume_set",
        "mute":          "mute",
        "unmute":        "unmute",
        "screenshot":    "screenshot",
        "shutdown":      "shutdown",
        "restart":       "restart",
        "lock":          "lock",
        "type_text":     "type",
    }

    cmd_type = action_map.get(action)
    if cmd_type:
        return execute_command(cmd_type, target)

    return None

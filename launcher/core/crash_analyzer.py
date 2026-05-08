import os
import re
from launcher.utils.logger import get_logger

log = get_logger("CrashAnalyzer")

class CrashAnalyzer:
    """
    Advanced industrial-grade log and crash analyzer for Minecraft.
    Parses latest.log and crash-reports to diagnose over 50 common issues.
    """

    PATTERNS = [
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError"),
            "title": "Нехватка оперативной памяти (ОЗУ)",
            "solution": "Увеличьте максимальное количество выделенной памяти (RAM Max) во вкладке 'Настройки' или закройте фоновые программы (браузер, антивирус)."
        },
        {
            "regex": re.compile(r"java\.lang\.UnsupportedClassVersionError.*?class file version (\d+\.\d+)"),
            "title": "Неподдерживаемая версия Java",
            "solution": "Вы используете несовместимую версию Java. Для старых версий (1.8-1.12) нужна Java 8, для 1.16.5 - Java 11, для 1.17+ - Java 17/21. Установите правильную версию и укажите путь к ней в настройках."
        },
        {
            "regex": re.compile(r"ModResolutionException.*?Missing dependencies: (.*)"),
            "title": "Отсутствуют зависимости модов",
            "solution": "Установленному моду не хватает другого мода для работы. Установите требуемые библиотеки: {group}"
        },
        {
            "regex": re.compile(r"DuplicateModsFoundException: Duplicate mods found: (.*)"),
            "title": "Дубликаты модов",
            "solution": "В папке mods найдено несколько копий одного и того же мода. Удалите дубликат: {group}"
        },
        {
            "regex": re.compile(r"java\.lang\.NoSuchMethodError: (.*)"),
            "title": "Конфликт версий мода/API",
            "solution": "Один из модов пытается вызвать метод, которого больше не существует. Вероятно, вы используете мод для другой версии Minecraft, либо конфликтуют два похожих мода."
        },
        {
            "regex": re.compile(r"org\.lwjgl\.LWJGLException: Pixel format not accelerated"),
            "title": "Ошибка драйверов видеокарты",
            "solution": "Проблема с OpenGL. Обновите драйвера вашей видеокарты (NVIDIA, AMD или Intel) с официального сайта."
        },
        {
            "regex": re.compile(r"Failed to write core dump\. Minidumps are not enabled"),
            "title": "Глубокий сбой JVM (Core Dump)",
            "solution": "Сбой на уровне виртуальной машины Java или видеокарты. Убедитесь, что у вас 64-битная Java, обновите драйвера GPU и отключите оверлеи (Discord, RivaTuner)."
        },
        {
            "regex": re.compile(r"java\.net\.SocketException: Connection reset"),
            "title": "Разрыв соединения",
            "solution": "Сервер разорвал соединение или ваш интернет нестабилен. Попробуйте перезапустить роутер или использовать VPN/другой DNS."
        },
        {
            "regex": re.compile(r"Exception in server tick loop"),
            "title": "Падение внутреннего сервера",
            "solution": "Внутренний сервер игры упал. Обычно это вызвано кривым датапаком, поврежденным миром или тяжелым модом. Изучите краш-лог для подробностей."
        },
        {
            "regex": re.compile(r"com\.mojang\.authlib\.exceptions\.AuthenticationException"),
            "title": "Ошибка авторизации Mojang",
            "solution": "Не удалось связаться с серверами Mojang. Проверьте интернет-соединение или статус серверов авторизации. Возможно, требуется перелогиниться."
        },
        {
            "regex": re.compile(r"java\.lang\.ClassNotFoundException: (.*)"),
            "title": "Отсутствует класс Java",
            "solution": "Моду не удалось найти необходимый класс {group}. Убедитесь, что у вас установлены все требуемые API (например, Architectury или Cloth Config) правильных версий."
        },
        {
            "regex": re.compile(r"The game crashed whilst rendering overlay"),
            "title": "Ошибка рендера оверлея",
            "solution": "Проблема связана с отрисовкой экрана загрузки или интерфейса игры модом. Часто возникает из-за модов на главное меню (CustomMainMenu, FancyMenu). Обновите или удалите их."
        },
        {
            "regex": re.compile(r"Exception in thread \"main\" java\.lang\.SecurityException: Forbidden"),
            "title": "Блокировка системы безопасности",
            "solution": "Антивирус или настройки системы Windows (DEP, UAC) блокируют запуск Java. Добавьте Java и Minecraft в исключения вашего антивируса."
        },
        {
            "regex": re.compile(r"cpw\.mods\.fml\.common\.LoaderException: java\.lang\.NoClassDefFoundError"),
            "title": "Фатальная ошибка Forge",
            "solution": "Устаревшая ошибка загрузчика Forge. Возникает из-за конфликта между очень старыми модами (1.7.10/1.12.2). Проверьте совместимость модов в сборке."
        },
        {
            "regex": re.compile(r"org\.spongepowered\.asm\.mixin\.throwables\.MixinApplyError"),
            "title": "Сбой Mixin (Внутренний конфликт)",
            "solution": "Два или более модов пытаются изменить один и тот же участок кода игры (ошибка Mixin). Найдите конфликтующие моды в краш-репорте (строки ниже MixinApplyError) и удалите один из них."
        },
        {
            "regex": re.compile(r"java\.net\.BindException: Address already in use: bind"),
            "title": "Порт уже используется",
            "solution": "Вы пытаетесь запустить локальный сервер или игру с пробросом портов, но порт 25565 уже занят другим процессом (например, сервером или uTorrent). Закройте мешающее приложение."
        },
        {
            "regex": re.compile(r"java\.lang\.StackOverflowError"),
            "title": "Переполнение стека (StackOverflowError)",
            "solution": "Произошло зацикливание в коде игры (часто из-за баганного мода или огромных механизмов). Попробуйте обновить моды или увеличить параметр -Xss в аргументах JVM."
        },
        {
            "regex": re.compile(r"net\.minecraftforge\.fml\.config\.ConfigFileTypeHandler\$ConfigLoadingException"),
            "title": "Поврежденный файл конфигурации",
            "solution": "Один из конфигурационных файлов мода поврежден. Перейдите в папку config внутри сборки и удалите недавно измененные файлы (они сгенерируются заново)."
        },
        {
            "regex": re.compile(r"java\.io\.FileNotFoundException: (.*) \(Отказано в доступе\)"),
            "title": "Отказано в доступе к файлу",
            "solution": "Антивирус или Windows заблокировали доступ к файлу {group}. Запустите лаунчер от имени Администратора или добавьте папку в исключения."
        },
        {
            "regex": re.compile(r"java\.lang\.NullPointerException: Cannot invoke (.*) because (.*) is null"),
            "title": "NullPointerException (NPE)",
            "solution": "Критический баг в коде одного из модов. Посмотрите краш-репорт, чтобы найти название сбойного мода, и удалите его или обновите."
        },
        {
            "regex": re.compile(r"org\.spongepowered\.asm\.mixin\.injection\.throwables\.InvalidInjectionException"),
            "title": "Ошибка инъекции Mixin",
            "solution": "Мод не смог внедриться в код игры. Обычно это означает, что версия мода не подходит для вашей версии Minecraft (или конфликтует с OptiFine/Rubidium)."
        },
        {
            "regex": re.compile(r"net\.fabricmc\.loader\.impl\.FormattedException: Mod resolution encountered an incompatible mod set"),
            "title": "Конфликт версий модов Fabric",
            "solution": "Установлены несовместимые моды Fabric. Откройте latest.log, чтобы увидеть точный список несовместимых версий и обновите/удалите их."
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: Java heap space"),
            "title": "Переполнение кучи (Heap Space)",
            "solution": "Сборка слишком тяжелая для текущих настроек памяти. Зайдите в 'Настройки' и увеличьте RAM Max."
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: Metaspace"),
            "title": "Переполнение Metaspace",
            "solution": "В игре установлено слишком много модов или сложные текстуры. Добавьте флаг -XX:MaxMetaspaceSize=512M (или больше) в аргументы JVM."
        },
        {
            "regex": re.compile(r"A fatal error has been detected by the Java Runtime Environment:"),
            "title": "Фатальный сбой JRE",
            "solution": "Внутренняя ошибка Java (часто из-за драйверов видеокарты Intel/AMD или битой плашки ОЗУ). Обновите драйверы или установите другую сборку Java (Adoptium, Corretto)."
        }
    ]

    @staticmethod
    def _read_file_tail(filepath, lines=500):
        """Reads the last N lines of a file to save memory on huge logs."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()
                return "".join(content[-lines:])
        except Exception as e:
            log.error(f"Failed to read log {filepath}: {e}")
            return ""

    @staticmethod
    def analyze_crash(instance_dir):
        """
        Analyzes latest.log and the most recent crash-report.
        Returns a dict with title and solution if a known crash is found.
        """
        log_dir = os.path.join(instance_dir, "logs")
        latest_log = os.path.join(log_dir, "latest.log")

        crash_dir = os.path.join(instance_dir, "crash-reports")

        content_to_analyze = ""

        # 1. Grab latest.log tail
        if os.path.exists(latest_log):
            content_to_analyze += CrashAnalyzer._read_file_tail(latest_log, 300)

        # 2. Grab newest crash report if it exists
        if os.path.exists(crash_dir):
            try:
                reports = [os.path.join(crash_dir, f) for f in os.listdir(crash_dir) if f.endswith(".txt")]
                if reports:
                    newest_report = max(reports, key=os.path.getmtime)
                    content_to_analyze += "\n" + CrashAnalyzer._read_file_tail(newest_report, 200)
            except Exception as e:
                log.error(f"Error accessing crash reports: {e}")

        if not content_to_analyze:
            return None

        # Analyze
        for pattern in CrashAnalyzer.PATTERNS:
            match = pattern["regex"].search(content_to_analyze)
            if match:
                solution = pattern["solution"]
                # Inject regex groups if the solution template supports it
                if "{group}" in solution and match.groups():
                    solution = solution.format(group=match.group(1))

                log.info(f"Crash Analyzer found issue: {pattern['title']}")
                return {
                    "title": pattern["title"],
                    "solution": solution,
                    "raw_match": match.group(0)
                }

        # Fallback generic detection
        if "Exception" in content_to_analyze or "Error" in content_to_analyze:
            return {
                "title": "Неизвестная ошибка (Смотрите логи)",
                "solution": "Игра завершилась с ошибкой, но лаунчер не смог точно определить причину. Пожалуйста, проверьте папку crash-reports или отправьте latest.log администратору.",
                "raw_match": "N/A"
            }

        return None

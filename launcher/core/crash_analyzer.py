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
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: Requested array size exceeds VM limit"),
            "title": "Превышен лимит массива (OutOfMemoryError)",
            "solution": "Мод или игра попыталась выделить слишком большой объем памяти за одну операцию. Попробуйте выделить больше ОЗУ или удалить тяжелые моды."
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: GC overhead limit exceeded"),
            "title": "Сборщик мусора перегружен",
            "solution": "Java тратит более 98% времени на очистку памяти (GC) и менее 2% на работу игры. Увеличьте RAM или используйте ZGC/ShenandoahGC."
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: unable to create new native thread"),
            "title": "Лимит системных потоков",
            "solution": "В системе закончились ресурсы для создания новых потоков. Увеличьте файл подкачки Windows, закройте лишние программы или обновите ОС."
        },
        {
            "regex": re.compile(r"java\.lang\.OutOfMemoryError: Direct buffer memory"),
            "title": "Переполнение Direct Buffer",
            "solution": "Нехватка 'нативной' памяти (DirectMemory). Добавьте параметр -XX:MaxDirectMemorySize=2G в аргументы JVM."
        },
        {
            "regex": re.compile(r"java\.io\.IOException: No space left on device"),
            "title": "Нет места на диске",
            "solution": "У вас закончилось место на диске. Очистите кэш лаунчера (настройки -> очистка) или удалите лишние файлы с диска."
        },
        {
            "regex": re.compile(r"java\.util\.zip\.ZipException: error in opening zip file"),
            "title": "Поврежденный архив (Мод или Библиотека)",
            "solution": "Один из скачанных .jar файлов (мод или библиотека) поврежден. Попробуйте удалить моды, установленные последними, или запустите проверку кэша лаунчера."
        },
        {
            "regex": re.compile(r"java\.lang\.UnsatisfiedLinkError: (.*)"),
            "title": "Отсутствует нативная библиотека (UnsatisfiedLinkError)",
            "solution": "Игре не хватает файла .dll или .so ({group}). Перекачайте библиотеки (возможно, антивирус удалил критический файл)."
        },
        {
            "regex": re.compile(r"org\.lwjgl\.opengl\.OpenGLException: Cannot create OpenGL context"),
            "title": "Сбой OpenGL (Драйверы видеокарты)",
            "solution": "Не удалось инициализировать видеокарту. Обновите видеодрайверы (AMD/NVIDIA/Intel). Если у вас старый ПК, возможно, видеокарта не поддерживает новые версии OpenGL (требуется 3.2+ или 4.4+ для новых версий)."
        },
        {
            "regex": re.compile(r"EXCEPTION_ACCESS_VIOLATION \(0xc0000005\)"),
            "title": "EXCEPTION_ACCESS_VIOLATION (Сбой драйвера)",
            "solution": "Фатальная ошибка доступа к памяти. В 90% случаев виноват драйвер видеокарты, особенно Intel HD Graphics или AMD. Обновите или, наоборот, откатите драйвер."
        },
        {
            "regex": re.compile(r"ig9icd64\.dll"),
            "title": "Конфликт с Intel Graphics",
            "solution": "Ошибка в модуле драйвера Intel (ig9icd64.dll). Зайдите на сайт Intel и скачайте последнюю версию драйвера для вашей встроенной видеокарты."
        },
        {
            "regex": re.compile(r"atio6axx\.dll"),
            "title": "Конфликт драйверов AMD",
            "solution": "Ошибка в драйвере видеокарты AMD (atio6axx.dll). Обновите Radeon Adrenalin Edition до последней стабильной (WHQL) версии."
        },
        {
            "regex": re.compile(r"nvoglv64\.dll"),
            "title": "Конфликт драйверов NVIDIA",
            "solution": "Сбой в драйвере NVIDIA OpenGL. Отключите наложение (Overlay) в GeForce Experience, закройте MSI Afterburner/RivaTuner или обновите драйвер."
        },
        {
            "regex": re.compile(r"java\.lang\.IllegalStateException: GLFW error (\d+): (.*)"),
            "title": "Ошибка создания окна (GLFW)",
            "solution": "Не удалось создать окно игры. Ошибка {group}. Обновите драйверы видеокарты."
        },
        {
            "regex": re.compile(r"net\.minecraft\.client\.renderer\.StitcherException: Unable to fit: (.*) - size: (\d+)x(\d+)"),
            "title": "Огромные текстуры (StitcherException)",
            "solution": "Разрешение ресурспака или текстур мода {group} превышает лимит вашей видеокарты. Используйте текстуры меньшего разрешения."
        },
        {
            "regex": re.compile(r"java\.lang\.IllegalArgumentException: Multiple entries with same key: (.*)"),
            "title": "Конфликт регистраций (Одинаковый ключ)",
            "solution": "Два разных мода пытаются зарегистрировать предмет или блок под одним и тем же именем: {group}. Ознакомьтесь с логами для поиска виновника."
        },
        {
            "regex": re.compile(r"net\.minecraftforge\.fml\.common\.LoaderExceptionModCrash: Caught exception from (.*)"),
            "title": "Фатальная ошибка мода Forge",
            "solution": "Мод {group} вызвал критическую ошибку во время загрузки. Проверьте, совместима ли его версия с вашей версией Minecraft, и нет ли конфликтов с другими модами."
        },
        {
            "regex": re.compile(r"net\.fabricmc\.loader\.impl\.discovery\.ModResolutionException: Mod discovery failed!"),
            "title": "Ошибка обнаружения модов Fabric",
            "solution": "Fabric Loader не смог найти или распознать некоторые моды. Возможно, в папке mods лежат файлы для Forge, или один из модов сильно поврежден."
        },
        {
            "regex": re.compile(r"net\.fabricmc\.loader\.impl\.util\.ExceptionUtil\$WrappedException: java\.io\.IOException: error reading zip file (.*)"),
            "title": "Битый Fabric Мод",
            "solution": "Мод {group} поврежден (вероятно, загрузился не до конца). Скачайте и установите его заново."
        },
        {
            "regex": re.compile(r"OptiFine is not supported on this version"),
            "title": "Несовместимость OptiFine",
            "solution": "OptiFine не поддерживается в данной сборке. Попробуйте заменить его на связку Sodium/Rubidium + Oculus, либо обновите версию OptiFine."
        },
        {
            "regex": re.compile(r"java\.lang\.AbstractMethodError: (.*)"),
            "title": "Конфликт API (AbstractMethodError)",
            "solution": "Мод вызывает метод {group}, который был изменен в новой версии игры или библиотеки. Проверьте актуальность модов. Если вы используете OptiFine, попробуйте его удалить."
        },
        {
            "regex": re.compile(r"org\.spongepowered\.asm\.mixin\.injection\.throwables\.InjectionError: Critical injection failure: (.*)"),
            "title": "Критическая ошибка инъекции (Mixin)",
            "solution": "Один из модов (через Mixin: {group}) не смог внедриться в базовый код игры. Убедитесь, что моды совместимы друг с другом. Очень часто это проблема конфликта модов оптимизации."
        },
        {
            "regex": re.compile(r"java\.lang\.RuntimeException: Multiplexing block definition error"),
            "title": "Ошибка регистрации блоков",
            "solution": "Сборка превысила внутренний лимит блоков (или мод неправильно регистрирует блок). Требуется мод JustEnoughIDs (для старых версий 1.12.2)."
        },
        {
            "regex": re.compile(r"java\.io\.EOFException: Unexpected end of ZLIB input stream"),
            "title": "Поврежденный файл сохранения (EOFException)",
            "solution": "Ваш файл мира, настроек (options.txt) или серверный пакет был поврежден во время записи (например, отключился свет). Удалите options.txt или восстановите мир из бэкапа."
        },
        {
            "regex": re.compile(r"net\.minecraft\.util\.ReportedException: Loading NBT data"),
            "title": "Поврежденный NBT (Чанки или Игрок)",
            "solution": "Minecraft не смог прочитать файл данных чанка или игрока. Если это ваш одиночный мир, возможно, он поврежден. Попробуйте утилиты RegionFixer."
        },
        {
            "regex": re.compile(r"java\.lang\.IllegalArgumentException: Cannot get property (.*) as it does not exist in (.*)"),
            "title": "Сбой свойств блока (BlockState)",
            "solution": "Мод попытался получить несуществующее свойство {group} для блока {group}. Проблема несовместимости мода с вашей версией Minecraft."
        },
        {
            "regex": re.compile(r"java\.lang\.ArrayIndexOutOfBoundsException: (\d+)"),
            "title": "Выход за пределы массива",
            "solution": "Баг внутри одного из модов или старой версии Forge (ошибка доступа к индексу {group}). Поищите обновление для проблемного мода."
        },
        {
            "regex": re.compile(r"java\.lang\.ArithmeticException: (.*)"),
            "title": "Арифметическая ошибка (ArithmeticException)",
            "solution": "Мод допустил математическую ошибку (например, деление на ноль: {group}). Это проблема разработчика мода, сообщите ему об ошибке."
        },
        {
            "regex": re.compile(r"java\.util\.ConcurrentModificationException"),
            "title": "Сбой многопоточности (CME)",
            "solution": "Два разных процесса (или мода) попытались одновременно изменить один список в игре. Обычно это случайный сбой, просто перезапустите игру."
        },
        {
            "regex": re.compile(r"org\.yaml\.snakeyaml\.parser\.ParserException: (.*)"),
            "title": "Сломанный YAML конфиг",
            "solution": "Файл настроек в формате .yaml сломан или содержит опечатки. Ошибка: {group}. Зайдите в папку config и исправьте/удалите проблемный файл."
        },
        {
            "regex": re.compile(r"com\.google\.gson\.JsonSyntaxException: (.*)"),
            "title": "Сломанный JSON конфиг",
            "solution": "Файл настроек (например, whitelist.json или конфиг мода) имеет неправильный синтаксис: {group}. Удалите его, чтобы игра сгенерировала новый."
        },
        {
            "regex": re.compile(r"io\.netty\.channel\.AbstractChannel\$AnnotatedConnectException: Connection refused: no further information"),
            "title": "Сервер не отвечает (Connection refused)",
            "solution": "Локальный или удаленный сервер выключен, либо его блокирует брандмауэр/антивирус. Проверьте IP и порт."
        },
        {
            "regex": re.compile(r"java\.lang\.IllegalAccessError: (.*)"),
            "title": "Ошибка доступа к методу (IllegalAccessError)",
            "solution": "Один мод пытается использовать приватный метод другого ({group}). Возможна несовместимость версий двух разных модов."
        },
        {
            "regex": re.compile(r"java\.lang\.IncompatibleClassChangeError: (.*)"),
            "title": "Сбой архитектуры классов (ICCE)",
            "solution": "Структура класса {group} была изменена (например, класс стал интерфейсом). Это фатальная ошибка совместимости мода с ядром игры."
        },
        {
            "regex": re.compile(r"java\.lang\.ClassCastException: (.*) cannot be cast to (.*)"),
            "title": "Неверный тип объекта (ClassCastException)",
            "solution": "Мод пытался преобразовать объект типа {group} в несовместимый тип. Баг разработчика мода."
        },
        {
            "regex": re.compile(r"java\.lang\.UnsupportedClassVersionError: (.*) has been compiled by a more recent version of the Java Runtime \(class file version (\d+\.\d+)\), this version of the Java Runtime only recognizes class file versions up to (\d+\.\d+)"),
            "title": "Критическая несовместимость Java",
            "solution": "Этот мод или версия Minecraft ({group}) скомпилирована для более новой Java, но вы пытаетесь использовать старую (например, запускаете 1.20.1 на Java 8). Установите Java 17+ в настройках."
        },
        {
            "regex": re.compile(r"net\.minecraftforge\.fml\.loading\.moddiscovery\.ModFileParser\$ModFileParserException: (.*)"),
            "title": "NullPointerException (Forge)",
            "solution": "Forge столкнулся с NPE во время парсинга файла мода: {group}. Файл поврежден (скорее всего, не докачался) или мод несовместим с вашей версией Forge. Перекачайте мод."
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

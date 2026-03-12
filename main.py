# -*- coding: utf-8 -*-
import os
import sys
import threading
import traceback
from datetime import datetime
import queue
import subprocess

# === ПОЛНОЕ ОТКЛЮЧЕНИЕ ВСЕХ ЛОГОВ KIVY ===
import os

os.environ['KIVY_NO_FILELOG'] = '1'  # Отключаем файл kivy_*.txt
os.environ['KIVY_NO_CONSOLELOG'] = '1'  # Отключаем консольные логи Kivy
os.environ['KIVY_LOG_MODE'] = 'MIXED'  # Минимальный режим

# Импортируем Config ДО любого импорта Kivy
from kivy.config import Config

Config.set('kivy', 'log_level', 'error')  # Только ошибки
Config.set('kivy', 'log_enable', '0')  # Полностью отключаем файл
Config.set('kivy', 'log_dir', '')  # Пустая папка для логов
Config.set('kivy', 'log_name', '')  # Пустое имя файла
# === КОНЕЦ БЛОКА ОТКЛЮЧЕНИЯ ===

# === УПРОЩЕННОЕ ЛОГИРОВАНИЕ (ТОЛЬКО НАШ ФАЙЛ) ===
import logging

# Удаляем все существующие обработчики
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Настраиваем ТОЛЬКО файловый логгер
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='debug.log',
    filemode='a',
    encoding='utf-8',
    force=True  # Принудительно перезаписываем настройки
)

# ВАЖНО: Отключаем передачу логов в родительские логгеры
logging.getLogger().propagate = False

# Добавляем разделитель
logging.info("=" * 60)
logging.info(f"НОВЫЙ ЗАПУСК ПРОГРАММЫ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info("=" * 60)
# === КОНЕЦ НАСТРОЙКИ ЛОГИРОВАНИЯ ===

# Фикс для работы в .exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get('PATH', '')
    logging.info(f"Запуск из .exe, путь: {application_path}")
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Запуск из скрипта, путь: {application_path}")


# Функция для поиска ffmpeg
def find_ffmpeg():
    """Поиск ffmpeg в системе"""
    possible_paths = [
        "C:\\ffmpeg-8.0.1-essentials_build\\bin\\ffmpeg.exe",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        os.path.join(application_path, 'ffmpeg.exe'),
        os.path.join(application_path, 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(application_path, 'bin', 'ffmpeg.exe'),
    ]

    try:
        result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            path_from_where = result.stdout.strip().split('\n')[0]
            if os.path.exists(path_from_where):
                possible_paths.append(path_from_where)
    except:
        pass

    for path in possible_paths:
        if os.path.exists(path):
            logging.info(f"FFmpeg найден: {path}")
            return path

    logging.error("FFmpeg не найден!")
    return None


FFMPEG_PATH = find_ffmpeg()

# Импорты Kivy должны быть после настройки логирования
try:
    from kivy.clock import Clock
    from kivy.metrics import dp
    from kivy.core.clipboard import Clipboard
    from kivy.core.window import Window
    from kivy.core.text import LabelBase
    from kivy.config import Config

    # KivyMD импорты
    from kivymd.app import MDApp
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.floatlayout import MDFloatLayout
    from kivymd.uix.label import MDLabel
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.button import MDRaisedButton, MDFlatButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.list import MDList, ThreeLineIconListItem, IconLeftWidget
    from kivymd.uix.progressbar import MDProgressBar
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.selectioncontrol import MDCheckbox
    from kivymd.uix.snackbar import Snackbar
    from kivymd.uix.toolbar import MDTopAppBar
    from kivymd.uix.scrollview import MDScrollView
    from kivymd.uix.tab import MDTabs, MDTabsBase
    from kivymd.uix.menu import MDDropdownMenu
    from kivy.uix.filechooser import FileChooserListView
    from kivy.uix.popup import Popup

    # Принудительно импортируем иконки (для .exe)
    from kivymd.icon_definitions import md_icons

    logging.info(f"Загружено иконок: {len(md_icons)}")

    logging.info("Все импорты Kivy/MD успешно загружены")
except Exception as e:
    logging.error(f"Ошибка при импорте Kivy: {str(e)}")
    logging.error(traceback.format_exc())
    sys.exit(1)

# Импорт yt-dlp
try:
    import yt_dlp

    logging.info("yt-dlp успешно загружен")
    logging.info(f"yt-dlp версия: {yt_dlp.version.__version__}")
except Exception as e:
    logging.error(f"Ошибка при импорте yt-dlp: {str(e)}")
    yt_dlp = None


# ... остальной код вашего приложения остается без изменений ...

class LoggerStub:
    def debug(self, msg):
        logging.debug(f"yt-dlp: {msg}")

    def warning(self, msg):
        logging.warning(f"yt-dlp: {msg}")

    def error(self, msg):
        logging.error(f"yt-dlp: {msg}")


class FolderChooserPopup(Popup):
    def __init__(self, callback, **kwargs):
        try:
            super().__init__(**kwargs)
            self.callback = callback
            self.title = 'Выберите папку для сохранения'
            self.size_hint = (0.9, 0.9)

            initial_path = os.path.expanduser('~')
            if not os.path.exists(initial_path):
                initial_path = os.path.dirname(application_path)

            layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

            self.filechooser = FileChooserListView(
                path=initial_path,
                dirselect=True,
                size_hint_y=0.8
            )
            layout.add_widget(self.filechooser)

            btn_layout = MDBoxLayout(size_hint_y=0.1, spacing=10)
            btn_layout.add_widget(MDRaisedButton(
                text='Выбрать',
                on_release=self.select_folder
            ))
            btn_layout.add_widget(MDFlatButton(
                text='Отмена',
                on_release=self.dismiss
            ))
            layout.add_widget(btn_layout)

            self.add_widget(layout)
            logging.debug("FolderChooserPopup создан")
        except Exception as e:
            logging.error(f"Ошибка при создании FolderChooserPopup: {str(e)}")

    def select_folder(self, *args):
        try:
            if self.filechooser.selection:
                self.callback(self.filechooser.selection[0])
            self.dismiss()
        except Exception as e:
            logging.error(f"Ошибка при выборе папки: {str(e)}")


class VideoInfoCard(MDCard):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            self.orientation = "vertical"
            self.padding = dp(16)
            self.spacing = dp(8)
            self.size_hint_y = None
            self.height = dp(280)
            self.radius = dp(12)
            self.elevation = 1
            self.add_widget(MDLabel(text="Введите ссылку", halign="center"))
            logging.debug("VideoInfoCard создан")
        except Exception as e:
            logging.error(f"Ошибка при создании VideoInfoCard: {str(e)}")

    def update_info(self, info):
        try:
            self.clear_widgets()
            if not info:
                self.add_widget(MDLabel(text="Информация не доступна", halign="center"))
                return

            title = info.get('title', 'Без названия')
            self.add_widget(MDLabel(
                text=f"[b]{title[:60]}[/b]",
                markup=True,
                size_hint_y=None,
                height=dp(40)
            ))

            duration = info.get('duration', 0)
            duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"

            # Создаем строки с иконками вместо эмодзи
            self.add_info_row("clock-outline", f"Длительность: {duration_str}")
            self.add_info_row("account", f"Автор: {info.get('uploader', 'N/A')[:30]}")
            self.add_info_row("eye", f"Просмотров: {info.get('view_count', 0):,}")
            self.add_info_row("web", f"Платформа: {info.get('extractor_key', 'N/A')}")

            logging.debug("VideoInfoCard обновлен")
        except Exception as e:
            logging.error(f"Ошибка при обновлении VideoInfoCard: {str(e)}")

    def add_info_row(self, icon_name, text):
        """Вспомогательный метод для создания строки с иконкой и текстом"""
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(25),
            spacing=dp(8)
        )

        # Иконка
        icon = IconLeftWidget(
            icon=icon_name,
            theme_text_color="Secondary"
        )
        row.add_widget(icon)

        # Текст
        label = MDLabel(
            text=text,
            font_style="Caption",
            size_hint_x=0.9,
            theme_text_color="Secondary"
        )
        row.add_widget(label)

        self.add_widget(row)


class TabContent(MDFloatLayout, MDTabsBase):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            logging.debug(f"TabContent '{kwargs.get('title', 'unknown')}' создан")
        except Exception as e:
            logging.error(f"Ошибка при создании TabContent: {str(e)}")




class VideoDownloaderApp(MDApp):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            logging.info("Инициализация VideoDownloaderApp")

            self.gui_queue = queue.Queue()

            self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not os.path.exists(self.download_path):
                self.download_path = application_path

            self.downloading = False
            self.dialog = None
            self.available_formats = []
            self.selected_format = None
            self.video_info = None
            self.menu = None
            self.history_file = os.path.join(application_path, 'download_history.txt')

            # Проверяем наличие ffmpeg
            global FFMPEG_PATH
            if FFMPEG_PATH:
                logging.info(f"FFmpeg доступен по пути: {FFMPEG_PATH}")
            else:
                logging.warning("FFmpeg не найден! Комбинированные форматы могут не работать.")

            logging.info(f"Путь загрузки: {self.download_path}")
            logging.info(f"Файл истории: {self.history_file}")
        except Exception as e:
            logging.error(f"Ошибка в __init__: {str(e)}")
            logging.error(traceback.format_exc())

    def build(self):
        try:
            logging.info("Запуск build()")

            if getattr(sys, 'frozen', False):
                # В .exe режиме ищем иконку в sys._MEIPASS
                if hasattr(sys, '_MEIPASS'):
                    icon_path = os.path.join(sys._MEIPASS, 'videod.ico')
                else:
                    icon_path = os.path.join(os.path.dirname(sys.executable), 'videod.ico')
            else:
                # В режиме разработки ищем в папке проекта
                icon_path = os.path.join(application_path, 'videod.ico')

            if os.path.exists(icon_path):
                self.icon = icon_path
                logging.info(f"✅ Иконка загружена: {icon_path}")
            else:
                logging.warning(f"⚠️ Иконка не найдена по пути: {icon_path}")

            # Путь к стандартному шрифту эмодзи в Windows 10/11
            emoji_font_path = "C:\\Windows\\Fonts\\seguiemj.ttf"
            if os.path.exists(emoji_font_path):
                # Регистрируем шрифт с новым именем
                LabelBase.register(name='EmojiFont', fn_regular=emoji_font_path)
                # Устанавливаем этот шрифт как один из основных
                # Важно: оставляем запасной шрифт для обычных символов
                Config.set('kivy', 'default_font', [
                    'EmojiFont',
                    'data/fonts/DejaVuSans.ttf',
                    'data/fonts/Roboto-Regular.ttf'  # Запасной для KivyMD
                ])
                logging.info("✅ Шрифт с эмодзи (Segoe UI Emoji) успешно загружен и установлен по умолчанию.")
            else:
                logging.warning("⚠️ Шрифт Segoe UI Emoji не найден. Эмодзи могут не отображаться.")

            self.theme_cls.primary_palette = "Blue"
            icon_path = os.path.join(application_path, 'videod.ico')
            if os.path.exists(icon_path):
                self.icon = icon_path
                logging.info(f"Иконка загружена: {icon_path}")

            Clock.schedule_interval(self.process_gui_queue, 0.1)

            layout = MDBoxLayout(orientation="vertical")

            toolbar = MDTopAppBar(title="Video Downloader Pro")
            toolbar.right_action_items = [
                ["folder", lambda x: self.choose_folder()],
                ["history", lambda x: self.switch_to_history_tab()],
                ["information-outline", lambda x: self.show_about()]
            ]
            layout.add_widget(toolbar)

            self.tabs = MDTabs()
            layout.add_widget(self.tabs)
            self.setup_tabs()

            Clock.schedule_once(lambda dt: self.load_history(), 1)

            logging.info("build() завершен успешно")
            return layout

        except Exception as e:
            logging.error(f"Ошибка в build(): {str(e)}")
            logging.error(traceback.format_exc())
            return MDLabel(text=f"Ошибка запуска: {str(e)}", halign="center")

    def switch_to_history_tab(self):
        try:
            self.tabs.switch_tab("История")
        except Exception as e:
            logging.error(f"Ошибка при переключении вкладки: {str(e)}")

    def process_gui_queue(self, dt):
        try:
            while True:
                try:
                    task = self.gui_queue.get_nowait()
                    func = task.get('func')
                    args = task.get('args', ())
                    kwargs = task.get('kwargs', {})

                    if func:
                        func(*args, **kwargs)

                except queue.Empty:
                    break
        except Exception as e:
            logging.error(f"Ошибка при обработке очереди GUI: {str(e)}")

    def safe_gui_call(self, func, *args, **kwargs):
        self.gui_queue.put({
            'func': func,
            'args': args,
            'kwargs': kwargs
        })

    def setup_tabs(self):
        try:
            logging.info("Настройка вкладок")

            download_tab = TabContent(title="Скачать")
            scroll = MDScrollView()
            container = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12), size_hint_y=None)
            container.bind(minimum_height=container.setter('height'))

            self.url_input = MDTextField(hint_text="URL видео", mode="rectangle")
            container.add_widget(self.url_input)

            btn_box = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            btn_box.add_widget(MDRaisedButton(text="Вставить", on_release=self.paste_url))
            btn_box.add_widget(MDRaisedButton(text="Анализ", on_release=self.analyze_video))
            container.add_widget(btn_box)

            self.info_card = VideoInfoCard()
            container.add_widget(self.info_card)

            # Выбор разрешения
            resolution_box = MDBoxLayout(orientation="vertical", spacing=dp(5), size_hint_y=None, height=dp(100))
            resolution_box.add_widget(MDLabel(
                text="Доступные разрешения (выберите качество):",
                font_style="Caption",
                size_hint_y=None,
                height=dp(20)
            ))

            self.resolution_dropdown = MDRaisedButton(
                text="Выберите разрешение",
                on_release=self.open_resolution_menu,
                size_hint_y=None,
                height=dp(40),
                disabled=True
            )
            resolution_box.add_widget(self.resolution_dropdown)

            self.format_info_label = MDLabel(
                text="",
                font_style="Caption",
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Secondary"
            )
            resolution_box.add_widget(self.format_info_label)

            container.add_widget(resolution_box)

            folder_box = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))

            # Создаем горизонтальную строку для папки
            folder_row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(25),
                spacing=dp(8)
            )

            # Иконка папки
            folder_icon = IconLeftWidget(
                icon="folder",
                theme_text_color="Secondary"
            )
            folder_row.add_widget(folder_icon)

            # Текст пути
            self.folder_path_label = MDLabel(
                text=os.path.basename(self.download_path),
                font_style="Caption",
                size_hint_x=0.9
            )
            folder_row.add_widget(self.folder_path_label)

            folder_box.add_widget(folder_row)
            folder_box.add_widget(MDRaisedButton(
                text="Изменить",
                on_release=lambda x: self.choose_folder(),
                size_hint_x=None,
                width=dp(80)
            ))
            container.add_widget(folder_box)

            self.playlist_check = MDCheckbox(size_hint=(None, None), size=(dp(40), dp(40)))
            opt_box = MDBoxLayout(size_hint_y=None, height=dp(40))
            opt_box.add_widget(self.playlist_check)
            opt_box.add_widget(MDLabel(text="Скачать плейлист", font_style="Caption"))
            container.add_widget(opt_box)

            self.progress_bar = MDProgressBar(value=0, size_hint_y=None, height=dp(4))
            self.progress_label = MDLabel(text="Готов", halign="center", font_style="Caption", size_hint_y=None,
                                          height=dp(20))
            container.add_widget(self.progress_bar)
            container.add_widget(self.progress_label)

            self.download_btn = MDRaisedButton(text="СКАЧАТЬ", on_release=self.start_download)
            container.add_widget(self.download_btn)

            scroll.add_widget(container)
            download_tab.add_widget(scroll)
            self.tabs.add_widget(download_tab)

            history_tab = TabContent(title="История")
            self.history_scroll = MDScrollView()
            self.history_list = MDList()
            self.history_scroll.add_widget(self.history_list)

            clear_btn = MDFlatButton(
                text="Очистить историю",
                on_release=self.clear_history,
                pos_hint={"center_x": 0.5},
                size_hint=(0.5, None),
                height=dp(40)
            )

            history_layout = MDBoxLayout(orientation="vertical")
            history_layout.add_widget(self.history_scroll)
            history_layout.add_widget(clear_btn)

            history_tab.add_widget(history_layout)
            self.tabs.add_widget(history_tab)

            logging.info("Вкладки настроены успешно")

        except Exception as e:
            logging.error(f"Ошибка в setup_tabs(): {str(e)}")
            logging.error(traceback.format_exc())

    def open_resolution_menu(self, *args):
        try:
            if not self.available_formats:
                return

            menu_items = []
            for fmt in self.available_formats:
                if fmt.get('height'):
                    # Используем иконки вместо эмодзи
                    audio_icon = "volume-high" if fmt.get('has_audio') else "volume-off"
                    combined_icon = "lightning-bolt" if fmt.get('is_combined') else ""

                    # Текст с иконками (в KivyMD меню иконки добавляются отдельно)
                    text = f"{fmt['height']}p"

                    if fmt.get('video_fps') and fmt['video_fps'] > 30:
                        text += f" {fmt['video_fps']}fps"

                    if fmt.get('filesize'):
                        size_mb = fmt['filesize'] / (1024 * 1024)
                        text += f" {size_mb:.0f}MB"

                else:
                    text = f"{fmt.get('abr', '?')}kbps ({fmt['ext']})"
                    if fmt.get('filesize'):
                        size_mb = fmt['filesize'] / (1024 * 1024)
                        text += f" {size_mb:.0f}MB"

                menu_items.append({
                    "text": text,
                    "on_release": lambda x=fmt: self.select_resolution(x),
                })

            self.menu = MDDropdownMenu(
                caller=self.resolution_dropdown,
                items=menu_items,
                width_mult=4,
            )
            self.menu.open()
            logging.debug(f"Меню разрешений открыто, пунктов: {len(menu_items)}")
        except Exception as e:
            logging.error(f"Ошибка при открытии меню: {str(e)}")

    def select_resolution(self, fmt):
        try:
            self.selected_format = fmt

            if fmt.get('height'):
                # Используем текстовые индикаторы вместо эмодзи
                audio_indicator = " [A]" if fmt.get('has_audio') else " [NoA]"
                combined_indicator = " [C]" if fmt.get('is_combined') else ""
                button_text = f"{fmt['height']}p{audio_indicator}{combined_indicator}"
                if fmt.get('ext'):
                    button_text += f" ({fmt['ext']})"
            else:
                button_text = f"Аудио {fmt.get('abr', '?')}kbps ({fmt['ext']})"

            self.resolution_dropdown.text = button_text

            info_text = []
            if fmt.get('vcodec') and fmt['vcodec'] != 'none':
                info_text.append(f"Видео: {fmt['vcodec'].split('.')[0]}")
            if fmt.get('acodec') and fmt['acodec'] != 'none':
                info_text.append(f"Аудио: {fmt['acodec'].split('.')[0]}")
            if fmt.get('video_fps'):
                info_text.append(f"{fmt['video_fps']}fps")
            if fmt.get('audio_abr'):
                info_text.append(f"{fmt['audio_abr']}kbps")
            if fmt.get('format_note'):
                info_text.append(f"{fmt['format_note']}")
            if fmt.get('is_combined'):
                info_text.append("комбинированный")

            if fmt.get('filesize'):
                size_mb = fmt['filesize'] / (1024 * 1024)
                info_text.append(f"{size_mb:.1f}MB")

            self.format_info_label.text = " | ".join(info_text) if info_text else ""

            if self.menu:
                self.menu.dismiss()
            logging.info(f"Выбран формат: {button_text}")
        except Exception as e:
            logging.error(f"Ошибка при выборе формата: {str(e)}")

    def choose_folder(self, *args):
        try:
            popup = FolderChooserPopup(self.folder_selected)
            popup.open()
        except Exception as e:
            logging.error(f"Ошибка при выборе папки: {str(e)}")
            self.show_dialog("Ошибка", f"Не удалось открыть выбор папки: {str(e)}")

    def folder_selected(self, selection):
        try:
            if selection:
                self.download_path = selection
                self.folder_path_label.text = f"📁 {os.path.basename(self.download_path)}"
                logging.info(f"Папка сохранения изменена на: {self.download_path}")
        except Exception as e:
            logging.error(f"Ошибка при обновлении папки: {str(e)}")

    def paste_url(self, *args):
        try:
            self.url_input.text = Clipboard.paste()
            logging.debug("URL вставлен из буфера обмена")
        except Exception as e:
            logging.error(f"Ошибка при вставке: {str(e)}")
            self.show_dialog("Ошибка", "Не удалось вставить текст")

    def analyze_video(self, *args):
        try:
            url = self.url_input.text.strip()
            if not url:
                self.show_dialog("Ошибка", "Введите URL видео")
                return

            if yt_dlp is None:
                self.show_dialog("Ошибка", "Библиотека yt-dlp не загружена")
                return

            self.progress_label.text = "Анализ..."
            self.resolution_dropdown.disabled = True
            self.resolution_dropdown.text = "Выберите разрешение"
            self.format_info_label.text = ""

            logging.info(f"Начало анализа URL: {url}")
            threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

        except Exception as e:
            logging.error(f"Ошибка в analyze_video: {str(e)}")
            self.show_dialog("Ошибка", str(e))

    def _analyze_thread(self, url):
        try:
            logging.info("Запуск потока анализа")

            opts = {
                'quiet': True,
                'logger': LoggerStub(),
            }

            # Указываем путь к ffmpeg, если он найден
            global FFMPEG_PATH
            if FFMPEG_PATH:
                opts['ffmpeg_location'] = FFMPEG_PATH
                logging.info(f"Используем ffmpeg по пути: {FFMPEG_PATH}")

            if getattr(sys, 'frozen', False):
                cache_dir = os.path.join(application_path, 'cache')
                os.makedirs(cache_dir, exist_ok=True)
                opts['cachedir'] = cache_dir
                logging.info(f"Кэш-директория: {cache_dir}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                logging.info("Извлечение информации о видео...")
                info = ydl.extract_info(url, download=False)
                self.video_info = info

                # Получаем все форматы
                formats = info.get('formats', [])

                # Разделяем на видео и аудио потоки
                video_streams = {}
                audio_streams = {}

                for fmt in formats:
                    try:
                        format_id = fmt.get('format_id', '')
                        height = fmt.get('height')
                        vcodec = fmt.get('vcodec', 'none')
                        acodec = fmt.get('acodec', 'none')
                        filesize = fmt.get('filesize', 0)
                        ext = fmt.get('ext', 'unknown')
                        format_note = fmt.get('format_note', '')
                        fps = fmt.get('fps', 0)
                        abr = fmt.get('abr', 0)

                        has_video = vcodec != 'none'
                        has_audio = acodec != 'none'

                        if has_video and height:
                            if height not in video_streams:
                                video_streams[height] = []

                            video_streams[height].append({
                                'format_id': format_id,
                                'height': height,
                                'ext': ext,
                                'vcodec': vcodec,
                                'fps': fps,
                                'filesize': filesize,
                                'format_note': format_note,
                                'has_video': True,
                                'has_audio': has_audio
                            })

                        if has_audio and not has_video:
                            audio_key = abr if abr > 0 else format_id
                            if audio_key not in audio_streams or audio_streams[audio_key].get('filesize', 0) < filesize:
                                audio_streams[audio_key] = {
                                    'format_id': format_id,
                                    'abr': abr,
                                    'ext': ext,
                                    'acodec': acodec,
                                    'filesize': filesize,
                                    'format_note': format_note,
                                    'has_video': False,
                                    'has_audio': True
                                }

                    except Exception as e:
                        logging.warning(f"Ошибка при обработке формата: {str(e)}")
                        continue

                # Создаем комбинированные форматы
                available_formats = []
                sorted_heights = sorted(video_streams.keys(), reverse=True)

                for height in sorted_heights:
                    best_video = None
                    for video in video_streams[height]:
                        if not best_video:
                            best_video = video
                        else:
                            if video.get('filesize', 0) > best_video.get('filesize', 0):
                                best_video = video

                    if best_video:
                        if best_video['has_audio']:
                            available_formats.append({
                                'format_id': best_video['format_id'],
                                'height': height,
                                'ext': best_video['ext'],
                                'vcodec': best_video['vcodec'],
                                'acodec': best_video.get('acodec', 'unknown'),
                                'filesize': best_video['filesize'],
                                'format_note': f"{best_video['format_note']} (встроенное аудио)",
                                'has_video': True,
                                'has_audio': True,
                                'is_combined': False
                            })
                        else:
                            best_audio = None
                            for audio_key, audio in audio_streams.items():
                                if not best_audio:
                                    best_audio = audio
                                else:
                                    if audio.get('abr', 0) > best_audio.get('abr', 0):
                                        best_audio = audio

                            if best_audio:
                                combined_format_id = f"{best_video['format_id']}+{best_audio['format_id']}"
                                estimated_size = (best_video.get('filesize', 0) + best_audio.get('filesize', 0))

                                available_formats.append({
                                    'format_id': combined_format_id,
                                    'height': height,
                                    'ext': 'mp4',
                                    'vcodec': best_video['vcodec'],
                                    'acodec': best_audio['acodec'],
                                    'filesize': estimated_size,
                                    'format_note': f"{best_video.get('format_note', '')} + {best_audio.get('format_note', '')}",
                                    'has_video': True,
                                    'has_audio': True,
                                    'is_combined': True,
                                    'video_fps': best_video.get('fps', 0),
                                    'audio_abr': best_audio.get('abr', 0)
                                })
                            else:
                                available_formats.append({
                                    'format_id': best_video['format_id'],
                                    'height': height,
                                    'ext': best_video['ext'],
                                    'vcodec': best_video['vcodec'],
                                    'acodec': 'none',
                                    'filesize': best_video['filesize'],
                                    'format_note': f"{best_video['format_note']} (без звука)",
                                    'has_video': True,
                                    'has_audio': False,
                                    'is_combined': False
                                })

                for audio_key, audio in audio_streams.items():
                    if audio.get('abr', 0) > 0:
                        available_formats.append({
                            'format_id': audio['format_id'],
                            'height': None,
                            'abr': audio['abr'],
                            'ext': audio['ext'],
                            'acodec': audio['acodec'],
                            'filesize': audio['filesize'],
                            'format_note': f"Аудио {audio['abr']}kbps",
                            'has_video': False,
                            'has_audio': True,
                            'is_combined': False
                        })

                available_formats.sort(
                    key=lambda x: (
                        x.get('height', 0) if x.get('height') else 0,
                        x.get('abr', 0) if not x.get('height') else 0
                    ),
                    reverse=True
                )

                logging.info(f"Найдено комбинированных форматов: {len(available_formats)}")
                for fmt in available_formats:
                    if fmt.get('height'):
                        audio_status = "🔊" if fmt.get('has_audio') else "🔇"
                        combined_status = "⚡" if fmt.get('is_combined') else ""
                        logging.info(f"  - {fmt['height']}p {audio_status}{combined_status}")
                    else:
                        logging.info(f"  - Аудио {fmt.get('abr', '?')}kbps")

                self.safe_gui_call(self._update_after_analysis, info, available_formats)

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Ошибка при анализе: {error_msg}")
            logging.error(traceback.format_exc())
            self.safe_gui_call(self.show_dialog, "Ошибка анализа", error_msg[:200])

    def _update_after_analysis(self, info, available_formats):
        try:
            self.available_formats = available_formats
            self.info_card.update_info(info)
            self.set_status("Готов")

            if self.available_formats:
                self.resolution_dropdown.disabled = False
                self.select_resolution(self.available_formats[0])

                video_count = len([f for f in available_formats if f.get('height')])
                audio_count = len([f for f in available_formats if not f.get('height') and f.get('abr')])
                self.show_snackbar(f"Доступно: {video_count} видео, {audio_count} аудио")
            else:
                self.show_dialog("Информация", "Не найдены доступные форматы")
        except Exception as e:
            logging.error(f"Ошибка при обновлении после анализа: {str(e)}")

    def start_download(self, *args):
        try:
            url = self.url_input.text.strip()
            if not url or self.downloading:
                return

            if not self.selected_format:
                self.show_dialog("Ошибка", "Выберите формат для загрузки")
                return

            if yt_dlp is None:
                self.show_dialog("Ошибка", "Библиотека yt-dlp не загружена")
                return

            self.downloading = True
            self.download_btn.disabled = True
            logging.info(f"Начало загрузки: {url}, формат: {self.selected_format}")

            threading.Thread(target=self._download_thread, args=(url,), daemon=True).start()

        except Exception as e:
            logging.error(f"Ошибка в start_download: {str(e)}")
            self.show_dialog("Ошибка", str(e))

    def _download_thread(self, url):
        try:
            def clean_filename(filename):
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '_')
                return filename

            if self.selected_format.get('height'):
                quality_info = f"[{self.selected_format['height']}p]"
            elif self.selected_format.get('abr'):
                quality_info = f"[{self.selected_format['abr']}kbps]"
            else:
                quality_info = ""

            template = f'%(title)s {quality_info}.%(ext)s'

            opts = {
                'format': self.selected_format['format_id'],
                'outtmpl': os.path.join(self.download_path, template),
                'progress_hooks': [self.hook],
                'logger': LoggerStub(),
            }

            # Указываем путь к ffmpeg для загрузки
            global FFMPEG_PATH
            if FFMPEG_PATH:
                opts['ffmpeg_location'] = FFMPEG_PATH
                logging.info(f"Используем ffmpeg по пути: {FFMPEG_PATH}")

            if getattr(sys, 'frozen', False):
                cache_dir = os.path.join(application_path, 'cache')
                os.makedirs(cache_dir, exist_ok=True)
                opts['cachedir'] = cache_dir

            logging.info(f"Параметры загрузки: {opts}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

                title = self.video_info.get('title', 'Без названия')[:50]
                timestamp = datetime.now().strftime('%H:%M %d.%m.%Y')

                quality = self.selected_format.get('height', self.selected_format.get('abr', '?'))
                quality_type = "p" if self.selected_format.get('height') else "kbps"

                self.safe_gui_call(self._add_to_history, title, f"{quality}{quality_type}", timestamp)

                logging.info("Загрузка успешно завершена")

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Ошибка при загрузке: {error_msg}")
            logging.error(traceback.format_exc())
            self.safe_gui_call(self.show_dialog, "Ошибка загрузки", error_msg[:200])
        finally:
            self.downloading = False
            self.safe_gui_call(self.reset_ui)

    def _add_to_history(self, title, quality, timestamp):
        try:
            def clean_filename(filename):
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '_')
                return filename

            history_item = ThreeLineIconListItem(
                IconLeftWidget(icon="download"),
                text=clean_filename(title),
                secondary_text=f"Качество: {quality}",
                tertiary_text=f"Сохранено: {timestamp}"
            )

            self.history_list.add_widget(history_item)
            self.save_to_history(f"{title} - {quality} - {timestamp}")
            self.show_snackbar("✅ Загрузка завершена!")
        except Exception as e:
            logging.error(f"Ошибка при добавлении в историю: {str(e)}")

    def hook(self, d):
        try:
            if d['status'] == 'downloading':
                if d.get('total_bytes'):
                    p = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
                elif d.get('total_bytes_estimate'):
                    p = d.get('downloaded_bytes', 0) / d.get('total_bytes_estimate', 1) * 100
                else:
                    p = 0

                self.safe_gui_call(self.update_progress, p)

                if int(p) % 10 == 0 and int(p) > 0:
                    logging.debug(f"Прогресс загрузки: {p:.1f}%")

            elif d['status'] == 'finished':
                self.safe_gui_call(self._set_status_text, "Обработка...")
                logging.info("Загрузка завершена, начало обработки")
        except Exception as e:
            logging.error(f"Ошибка в hook: {str(e)}")

    def _set_status_text(self, text):
        self.progress_label.text = text

    def update_progress(self, val):
        try:
            self.progress_bar.value = val
            self.progress_label.text = f"Загрузка: {val:.1f}%"
        except Exception as e:
            logging.error(f"Ошибка при обновлении прогресса: {str(e)}")

    def set_status(self, txt):
        try:
            self.progress_label.text = txt
        except Exception as e:
            logging.error(f"Ошибка при установке статуса: {str(e)}")

    def reset_ui(self):
        try:
            self.download_btn.disabled = False
            self.progress_bar.value = 0
            self.progress_label.text = "Готов"
            logging.debug("UI сброшен")
        except Exception as e:
            logging.error(f"Ошибка при сбросе UI: {str(e)}")

    def save_to_history(self, text):
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(text + '\n')
            logging.debug(f"Сохранено в историю: {text}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении истории: {str(e)}")

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line:
                            parts = line.split(' - ')
                            if len(parts) >= 3:
                                item = ThreeLineIconListItem(
                                    IconLeftWidget(icon="download"),
                                    text=parts[0],
                                    secondary_text=parts[1],
                                    tertiary_text=parts[2]
                                )
                                self.history_list.add_widget(item)
                logging.info(f"История загружена из {self.history_file}")
        except Exception as e:
            logging.error(f"Ошибка при загрузке истории: {str(e)}")

    def clear_history(self, *args):
        try:
            self.history_list.clear_widgets()
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            self.show_snackbar("История очищена")
            logging.info("История очищена")
        except Exception as e:
            logging.error(f"Ошибка при очистке истории: {str(e)}")
            self.show_snackbar("Ошибка при очистке истории")

    def show_about(self):
        try:
            about_text = (
                "Video Downloader Pro\n"
                f"Версия: 1.0.2\n\n"
                f"Папка программы:\n{application_path}\n\n"
                "Поддерживаемые сайты:\n"
                "YouTube, VK, Rutube и многие другие"
            )
            self.show_dialog("О программе\n", about_text)
        except Exception as e:
            logging.error(f"Ошибка при показе информации: {str(e)}")

    def show_dialog(self, title, text):
        try:
            if self.dialog:
                self.dialog.dismiss()

            content = MDBoxLayout(orientation='vertical', spacing=dp(10), adaptive_height=True)
            content.add_widget(MDLabel(
                text=text,
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            ))

            self.dialog = MDDialog(
                title=title,
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        on_release=lambda x: self.dialog.dismiss()
                    )
                ]
            )
            self.dialog.open()
            logging.debug(f"Диалог показан: {title}")
        except Exception as e:
            logging.error(f"Ошибка при показе диалога: {str(e)}")

    def show_snackbar(self, text):
        try:
            snackbar = Snackbar()
            if hasattr(snackbar, 'text'):
                snackbar.text = text
            else:
                from kivymd.uix.label import MDLabel
                snackbar.add_widget(MDLabel(
                    text=text,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    halign="center"
                ))
            snackbar.open()
            logging.debug(f"Снэкбар: {text}")
        except Exception as e:
            logging.error(f"Ошибка при показе снэкбара: {str(e)}")


if __name__ == "__main__":
    try:
        logging.info("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")
        logging.info(f"Python версия: {sys.version}")
        logging.info(f"Платформа: {sys.platform}")
        logging.info(f"Путь приложения: {application_path}")

        if yt_dlp:
            logging.info(f"yt-dlp версия: {yt_dlp.version.__version__}")
        else:
            logging.error("yt-dlp не загружен!")

        app = VideoDownloaderApp()
        app.run()

    except Exception as e:
        logging.critical(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        logging.critical(traceback.format_exc())

        # В .exe версии просто логируем ошибку и выходим
        logging.critical("Программа завершилась с критической ошибкой")

        # Показываем сообщение только если есть консоль
        if hasattr(sys, 'stdin') and sys.stdin is not None:
            print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            print("Подробности в файле debug.log")
            input("Нажмите Enter для выхода...")

        sys.exit(1)

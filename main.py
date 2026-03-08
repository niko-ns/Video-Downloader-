# -*- coding: utf-8 -*-
import os
import threading
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard
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

import yt_dlp


class LoggerStub:
    def debug(self, msg): pass

    def warning(self, msg): pass

    def error(self, msg): pass


class VideoInfoCard(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(280)
        self.radius = dp(12)
        self.elevation = 1
        self.add_widget(MDLabel(text="Введите ссылку", halign="center"))

    def update_info(self, info):
        self.clear_widgets()
        if not info:
            self.add_widget(MDLabel(text="Информация не доступна", halign="center"))
            return

        title = info.get('title', 'Без названия')
        self.add_widget(MDLabel(text=f"[b]{title[:60]}[/b]", markup=True, size_hint_y=None, height=dp(40)))

        duration = info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"

        details = [
            f"⏱ Длительность: {duration_str}",
            f"👤 Автор: {info.get('uploader', 'N/A')[:30]}",
            f"👁 Просмотров: {info.get('view_count', 0):,}",
            f"🌐 Платформа: {info.get('extractor_key', 'N/A')}"
        ]
        for text in details:
            self.add_widget(MDLabel(text=text, font_style="Caption", size_hint_y=None, height=dp(25)))


class TabContent(MDFloatLayout, MDTabsBase):
    pass


class VideoDownloaderApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.downloading = False
        self.dialog = None

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        layout = MDBoxLayout(orientation="vertical")
        layout.add_widget(MDTopAppBar(title="Video Downloader Pro", elevation=4))

        self.tabs = MDTabs()
        layout.add_widget(self.tabs)
        self.setup_tabs()
        return layout

    def setup_tabs(self):
        # Вкладка загрузки
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

        self.download_btn = MDRaisedButton(text="СКАЧАТЬ", pos_hint={"center_x": .5}, on_release=self.start_download)
        container.add_widget(self.download_btn)

        scroll.add_widget(container)
        download_tab.add_widget(scroll)
        self.tabs.add_widget(download_tab)

        # Вкладка истории
        history_tab = TabContent(title="История")
        self.history_list = MDList()
        h_scroll = MDScrollView()
        h_scroll.add_widget(self.history_list)
        history_tab.add_widget(h_scroll)
        self.tabs.add_widget(history_tab)

    def paste_url(self, *args):
        self.url_input.text = Clipboard.paste()

    def analyze_video(self, *args):
        url = self.url_input.text.strip()
        if not url: return
        self.progress_label.text = "Анализ..."
        threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

    def _analyze_thread(self, url):
        try:
            opts = {'quiet': True, 'logger': LoggerStub()}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                Clock.schedule_once(lambda dt: self.info_card.update_info(info))
                Clock.schedule_once(lambda dt: self.set_status("Готов"))
        except Exception as e:
            msg = str(e)
            Clock.schedule_once(lambda dt: self.show_dialog("Ошибка", msg[:100]))

    def start_download(self, *args):
        url = self.url_input.text.strip()
        if not url or self.downloading: return
        self.downloading = True
        self.download_btn.disabled = True
        threading.Thread(target=self._download_thread, args=(url,), daemon=True).start()

    def _download_thread(self, url):
        opts = {
            'format': 'best',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook],
            'logger': LoggerStub(),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                Clock.schedule_once(lambda dt: self.show_snackbar("Готово!"))
        except Exception as e:
            msg = str(e)
            Clock.schedule_once(lambda dt: self.show_dialog("Ошибка", msg[:100]))
        finally:
            self.downloading = False
            Clock.schedule_once(lambda dt: self.reset_ui())

    def hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
                Clock.schedule_once(lambda dt: self.update_progress(p))
            except:
                pass

    def update_progress(self, val):
        self.progress_bar.value = val
        self.progress_label.text = f"Загрузка: {val:.1f}%"

    def set_status(self, txt):
        self.progress_label.text = txt

    def reset_ui(self):
        self.download_btn.disabled = False
        self.progress_bar.value = 0
        self.progress_label.text = "Готов"

    def show_dialog(self, title, text):
        """Исправленный метод без использования свойства 'text'"""
        if self.dialog: self.dialog.dismiss()
        self.dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=MDLabel(text=text, theme_text_color="Secondary", adaptive_height=True),
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())]
        )
        self.dialog.open()

    def show_snackbar(self, text):
        """Исправленный метод для новых версий KivyMD"""
        try:
            # В новых версиях Snackbar ожидает виджет или специфический вызов
            Snackbar(text=text).open()
        except TypeError:
            # Резервный вариант, если свойство text вообще вырезано
            from kivymd.uix.label import MDLabel
            s = Snackbar()
            s.add_widget(MDLabel(text=text, theme_text_color="Custom", text_color=(1, 1, 1, 1)))
            s.open()


if __name__ == "__main__":
    VideoDownloaderApp().run()
import os
import threading

import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
import yt_dlp


def save_to_movies(path):
    """Video ko phone ki Movies/InstaDownloads folder (Gallery) mein copy karta hai."""
    from jnius import autoclass
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    CV = autoclass("android.content.ContentValues")
    media = autoclass("android.provider.MediaStore$Video$Media")
    FIS = autoclass("java.io.FileInputStream")
    FU = autoclass("android.os.FileUtils")
    cv = CV()
    cv.put("_display_name", os.path.basename(path))
    cv.put("mime_type", "video/mp4")
    cv.put("relative_path", "Movies/InstaDownloads")
    resolver = activity.getContentResolver()
    uri = resolver.insert(media.EXTERNAL_CONTENT_URI, cv)
    out = resolver.openOutputStream(uri)
    inp = FIS(path)
    FU.copy(inp, out)
    inp.close()
    out.close()


class InstaApp(App):
    def build(self):
        self.title = "Insta Downloader"
        root = BoxLayout(orientation="vertical", padding=12, spacing=10)
        root.add_widget(Label(text="Har line mein ek post/reel link paste karo",
                              size_hint_y=None, height=40))
        self.links = TextInput(hint_text="https://www.instagram.com/reel/...",
                               size_hint_y=0.35)
        root.add_widget(self.links)
        self.btn = Button(text="Download shuru karo", size_hint_y=None, height=64,
                          background_color=(0.88, 0.19, 0.42, 1))
        self.btn.bind(on_release=self.start)
        root.add_widget(self.btn)
        sv = ScrollView()
        self.log_label = Label(text="", size_hint_y=None, halign="left", valign="top")
        self.log_label.bind(
            width=lambda i, w: setattr(i, "text_size", (w, None)),
            texture_size=lambda i, s: setattr(i, "height", s[1]))
        sv.add_widget(self.log_label)
        root.add_widget(sv)
        return root

    def log(self, msg):
        Clock.schedule_once(lambda dt: setattr(
            self.log_label, "text", self.log_label.text + msg + "\n"))

    def start(self, *_):
        urls = [u.strip() for u in self.links.text.splitlines() if u.strip()]
        if not urls:
            self.log("Pehle kam se kam ek link paste karo.")
            return
        self.btn.disabled = True
        self.btn.text = "Download ho raha hai..."
        threading.Thread(target=self.run, args=(urls,), daemon=True).start()

    def run(self, urls):
        tmp = os.path.join(self.user_data_dir, "tmp")
        os.makedirs(tmp, exist_ok=True)
        ok = 0
        for i, url in enumerate(urls, 1):
            self.log("[%d/%d] %s" % (i, len(urls), url))
            files = []

            def hook(d):
                if d["status"] == "finished":
                    files.append(d["filename"])

            opts = {
                "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
                "format": "best[ext=mp4]/best",
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [hook],
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                for f in files:
                    save_to_movies(f)
                    os.remove(f)
                ok += 1
                self.log("   Done (Gallery > Movies > InstaDownloads)")
            except Exception as e:
                self.log("   Fail: %s" % str(e)[:200])
        self.log("Khatam: %d/%d" % (ok, len(urls)))
        Clock.schedule_once(self.reset_btn)

    def reset_btn(self, dt):
        self.btn.disabled = False
        self.btn.text = "Download shuru karo"


InstaApp().run()

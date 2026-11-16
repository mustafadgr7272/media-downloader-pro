import os
import threading
import flet as ft
import yt_dlp

def main(page: ft.Page):
    page.title = "Media Downloader Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    url_input = ft.TextField(
        label="Video / Ses Linkini Yapıştırın",
        hint_text="https://www.youtube.com/watch?v=...",
        border_radius=10,
        expand=True,
    )

    format_dropdown = ft.Dropdown(
        label="Format",
        value="mp4",
        options=[
            ft.dropdown.Option("mp4", "Video (MP4)"),
            ft.dropdown.Option("mp3", "Ses (MP3)"),
        ],
        width=180,
    )

    status_text = ft.Text("Hazır", size=14, color=ft.Colors.GREY_400)
    progress_bar = ft.ProgressBar(visible=False, width=300)

    def get_download_path():
        android_dl = "/storage/emulated/0/Download"
        if os.path.exists(android_dl) and os.access(android_dl, os.W_OK):
            return android_dl
        fallback = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(fallback, exist_ok=True)
        return fallback

    def progress_hook(d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").strip()
            status_text.value = f"İndiriliyor... {percent}"
            page.update()
        elif d["status"] == "finished":
            status_text.value = "Tamamlandı! İndirilenler klasörüne kaydedildi."
            status_text.color = ft.Colors.GREEN_400
            progress_bar.visible = False
            download_btn.disabled = False
            page.update()

    def run_download(url, fmt):
        try:
            save_dir = get_download_path()
            ydl_opts = {
                "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },
            }

            if fmt == "mp3":
                ydl_opts["format"] = "bestaudio/best"
            else:
                ydl_opts["format"] = "best[acodec!=none][vcodec!=none]/best[ext=mp4]/best"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as e:
            status_text.value = f"Hata: {str(e)}"
            status_text.color = ft.Colors.RED_400
            progress_bar.visible = False
            download_btn.disabled = False
            page.update()

    def on_download_click(e):
        url = url_input.value.strip()
        if not url:
            status_text.value = "Lütfen geçerli bir link girin!"
            status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        download_btn.disabled = True
        progress_bar.visible = True
        status_text.color = ft.Colors.BLUE_300
        status_text.value = "Bağlanıyor..."
        page.update()

        threading.Thread(
            target=run_download,
            args=(url, format_dropdown.value),
            daemon=True,
        ).start()

    ButtonClass = getattr(ft, "Button", None) or getattr(ft, "ElevatedButton")
    PaddingClass = getattr(ft, "Padding", None) or getattr(ft, "padding")

    download_btn = ButtonClass(
        "İNDİR",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_download_click,
        style=ft.ButtonStyle(
            padding=PaddingClass.symmetric(horizontal=30, vertical=15),
        ),
    )

    page.add(
        ft.Column(
            [
                ft.Text("Media Downloader Pro", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                ft.Row([url_input]),
                ft.Row(
                    [format_dropdown, download_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                progress_bar,
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )
    )

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)

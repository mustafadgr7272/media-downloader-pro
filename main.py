import os
import threading
import flet as ft
import yt_dlp

def format_bytes(size):
    if not size:
        return "?"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def main(page: ft.Page):
    page.title = "Media Downloader Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def get_default_path():
        android_dl = "/storage/emulated/0/Download"
        if os.path.exists(android_dl) and os.access(android_dl, os.W_OK):
            return android_dl
        fallback = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(fallback, exist_ok=True)
        return fallback

    selected_dir = {"path": get_default_path()}

    url_input = ft.TextField(
        label="Video / Ses Linkini Yapıştırın",
        hint_text="https://www.youtube.com/watch?v=...",
        border_radius=10,
        expand=True,
    )

    def on_format_change(e):
        quality_dropdown.disabled = (format_dropdown.value == "mp3")
        page.update()

    format_dropdown = ft.Dropdown(
        label="Format",
        value="mp4",
        options=[
            ft.dropdown.Option("mp4", "Video (MP4)"),
            ft.dropdown.Option("mp3", "Ses (MP3)"),
        ],
        on_change=on_format_change,
        expand=True,
    )

    quality_dropdown = ft.Dropdown(
        label="Görüntü Kalitesi",
        value="best",
        options=[
            ft.dropdown.Option("best", "En Yüksek"),
            ft.dropdown.Option("720", "720p (HD)"),
            ft.dropdown.Option("480", "480p (SD)"),
            ft.dropdown.Option("360", "360p (Düşük)"),
        ],
        expand=True,
    )

    path_text = ft.Text(
        f"Kayıt Yeri: {selected_dir['path']}",
        size=12,
        color=ft.Colors.GREY_400,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
        expand=True,
    )

    def on_dir_picked(e: ft.FilePickerResultEvent):
        if e.path:
            selected_dir["path"] = e.path
            path_text.value = f"Kayıt Yeri: {e.path}"
            page.update()

    dir_picker = ft.FilePicker(on_result=on_dir_picked)
    page.overlay.append(dir_picker)

    IconBtnClass = getattr(ft, "IconButton", None)
    pick_folder_btn = IconBtnClass(
        icon=ft.Icons.FOLDER_OPEN,
        tooltip="Kayıt Klasörü Seç",
        on_click=lambda _: dir_picker.get_directory_path(dialog_title="İndirilecek Klasörü Seçin"),
    )

    status_text = ft.Text("Hazır", size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
    progress_bar = ft.ProgressBar(visible=False, width=320)

    def progress_hook(d):
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").strip()
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            size_info = f"{format_bytes(downloaded)} / {format_bytes(total)}"
            status_text.value = f"İndiriliyor... {percent} ({size_info})"
            page.update()
        elif d["status"] == "finished":
            total = d.get("total_bytes") or d.get("downloaded_bytes", 0)
            status_text.value = f"Tamamlandı! ({format_bytes(total)})\nKlasör: {selected_dir['path']}"
            status_text.color = ft.Colors.GREEN_400
            progress_bar.visible = False
            download_btn.disabled = False
            page.update()

    def build_format_string(fmt, quality):
        if fmt == "mp3":
            return "bestaudio/best"
        if quality == "best":
            return "best[acodec!=none][vcodec!=none]/best[ext=mp4]/best"
        return (
            f"best[height<={quality}][acodec!=none][vcodec!=none]/"
            f"best[height<={quality}][ext=mp4]/"
            f"best[acodec!=none][vcodec!=none]/best"
        )

    def run_download(url, fmt, quality, save_dir):
        try:
            os.makedirs(save_dir, exist_ok=True)
            ydl_opts = {
                "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "format": build_format_string(fmt, quality),
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"]
                    }
                },
            }

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
        status_text.value = "Video bilgileri ve boyut alınıyor..."
        page.update()

        threading.Thread(
            target=run_download,
            args=(url, format_dropdown.value, quality_dropdown.value, selected_dir["path"]),
            daemon=True,
        ).start()

    ButtonClass = getattr(ft, "Button", None) or getattr(ft, "ElevatedButton")
    PaddingClass = getattr(ft, "Padding", None) or getattr(ft, "padding")

    download_btn = ButtonClass(
        "İNDİR",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_download_click,
        style=ft.ButtonStyle(
            padding=PaddingClass.symmetric(horizontal=35, vertical=15),
        ),
    )

    page.add(
        ft.Column(
            [
                ft.Text("Media Downloader Pro", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([url_input]),
                ft.Row(
                    [format_dropdown, quality_dropdown],
                    spacing=10,
                ),
                ft.Container(
                    content=ft.Row(
                        [path_text, pick_folder_btn],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=PaddingClass.symmetric(horizontal=12, vertical=6),
                    border_radius=10,
                    bgcolor=ft.Colors.WHITE10,
                ),
                ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                download_btn,
                ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
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

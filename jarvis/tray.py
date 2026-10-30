"""Optional Windows tray controls; importing this module starts no UI."""
import threading


class TrayController:
    """Thread-safe requested state, independent of tray GUI dependencies."""
    def __init__(self):
        self._lock = threading.Lock()
        self._muted = False
        self._exit = False

    def toggle_mute(self):
        with self._lock:
            self._muted = not self._muted
            return self._muted

    def request_exit(self):
        with self._lock:
            self._exit = True

    @property
    def muted(self):
        with self._lock:
            return self._muted

    @property
    def exit_requested(self):
        with self._lock:
            return self._exit


def run_tray(controller, worker_done=None):
    """Run a visible tray icon. Call from the GUI thread on Windows."""
    import pystray
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (64, 64), "#111827")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), outline="#6ee7b7", width=5)
    draw.text((25, 22), "J", fill="#ffffff")

    def toggle(icon, item):
        controller.toggle_mute()
        icon.update_menu()

    def quit_app(icon, item):
        controller.request_exit()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: "Включить микрофон" if controller.muted else "Выключить микрофон",
            toggle,
        ),
        pystray.MenuItem("Завершить JARVIS", quit_app),
    )
    icon = pystray.Icon("jarvis-local", image, "JARVIS Local", menu)

    def watch_worker():
        if worker_done is not None:
            worker_done.wait()
            controller.request_exit()
            icon.stop()

    if worker_done is not None:
        threading.Thread(target=watch_worker, daemon=True).start()
    icon.run()

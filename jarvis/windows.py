import time

class WindowsRecorder:
    def __init__(self):
        self.steps = []
        self.started = None
        self.listener = None
        self.last = None

    def start(self):
        from pynput import mouse
        self.started = time.monotonic()
        self.last = self.started
        def on_click(x, y, button, pressed):
            if pressed:
                now = time.monotonic()
                self.steps.append({'action': 'click', 'x': x, 'y': y, 'button': button.name, 'delay': round(now-self.last, 3)})
                self.last = now
        self.listener = mouse.Listener(on_click=on_click)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener.join(timeout=2)
        return self.steps


def replay(steps, dry_run=True):
    if not dry_run:
        import pyautogui
        pyautogui.FAILSAFE = True
    for step in steps:
        if step['action'] != 'click':
            raise ValueError('Unsupported action')
        delay = max(0, min(float(step['delay']), 10))
        if dry_run:
            print(f"WAIT {delay}s; CLICK ({step['x']}, {step['y']}) {step['button']}")
        else:
            time.sleep(delay)
            pyautogui.click(x=int(step['x']), y=int(step['y']), button=step['button'])

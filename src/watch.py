import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

class ReloadingHandler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        print(event)
        print("File changed, rebuilding...")
        os.system("python3 ./build_from_images.py 400")
        print("Done!")

observer = Observer()
handler = ReloadingHandler()
observer.schedule(handler, "./glyphs/", recursive = True)
observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

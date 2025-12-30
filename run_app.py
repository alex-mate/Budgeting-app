import os
import socket
import time
import webbrowser
from threading import Timer
from app import app

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

def port_is_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0

def open_browser_once():
    # HARD GUARD: if something calls this twice, open only once
    if os.environ.get("MATEBUDGET_BROWSER_OPENED") == "1":
        return
    os.environ["MATEBUDGET_BROWSER_OPENED"] = "1"

    # wait until server is listening
    for _ in range(80):  # ~8 seconds max
        if port_is_open(HOST, PORT):
            webbrowser.open(URL, new=1)  # new=1 = new tab if possible
            return
        time.sleep(0.1)

if __name__ == "__main__":
    Timer(0.5, open_browser_once).start()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

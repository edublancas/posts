"""Not working
"""

import websocket
import json


def on_message(ws, message):
    print(json.loads(message))


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Connection closed")


def on_open(ws):
    print("Connection opened")

    ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:9222/devtools/browser/81e4e0f3-9490-4b7c-a64b-c4543fae61a2",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()

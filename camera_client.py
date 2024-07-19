import asyncio
import websockets
import cv2
import time

async def send_video():
    while True:
        try:
            async with websockets.connect("ws://0.0.0.0:5000") as websocket:
                cap = cv2.VideoCapture(1)  # カメラからの映像をキャプチャする場合
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                cap.set(cv2.CAP_PROP_FPS, 30)

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    _, buffer = cv2.imencode('.jpg', frame)
                    await websocket.send(buffer.tobytes())
                    await asyncio.sleep(1 / 30)  # 約30fpsで送信

                cap.release()
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            print(f"Connection error: {e}")
            time.sleep(5)  # 5秒待ってから再接続を試みる

asyncio.get_event_loop().run_until_complete(send_video())

import asyncio
import websockets
import numpy as np
import cv2
import datetime

async def receive_video(uri):
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                frame_data = await websocket.recv()
                np_data = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
                if frame is not None:
                    # フレームのサイズを1280x720にリサイズ
                    frame = cv2.resize(frame, (1280, 720))

                    # 現在時刻を取得して左上に表示
                    #timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    #cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                    cv2.imshow("Received Video", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        finally:
            cv2.destroyAllWindows()

# クライアントのURIを指定して接続
uri = "ws://0.0.0.0:5000"
asyncio.get_event_loop().run_until_complete(receive_video(uri))

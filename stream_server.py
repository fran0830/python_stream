import asyncio
import websockets
import numpy as np
import cv2
import datetime
import threading
import queue
import time
import ffmpeg

connected_clients = set()
frame_queue = queue.Queue()
recording = True

async def register(websocket):
    connected_clients.add(websocket)

async def unregister(websocket):
    connected_clients.remove(websocket)

# 録画を行う為の関数
def video_recorder():
    while recording:
        # 10分毎に新しいファイル名を作成
        filename = f'video_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.mp4'
        process = (
            ffmpeg
            .input('pipe:0', format='rawvideo', pix_fmt='bgr24', s='1920x1080', framerate=30)
            .output(filename, pix_fmt='yuv420p', vcodec='libx264')
            .global_args('-y')
            .run_async(pipe_stdin=True)
        )
        
        start_time = time.time()
        while time.time() - start_time < 600:  # 10分 = 600秒
            if not frame_queue.empty():
                frame = frame_queue.get()
                if frame is not None:
                    process.stdin.write(frame.tobytes())

        process.stdin.close()
        process.wait()

async def video_stream(websocket, path):
    await register(websocket)
    try:
        while True:
            frame_data = await websocket.recv()
            np_data = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
            if frame is not None:
                # タイムスタンプを追加する
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                
                # フレームをキューに追加
                frame_queue.put(frame)

                # フレームをクライアントに送信
                encoded_frame = cv2.imencode('.jpg', frame)[1].tobytes()
                for client in connected_clients:
                    if client != websocket:
                        try:
                            await client.send(encoded_frame)
                        except websockets.exceptions.ConnectionClosed:
                            pass

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    finally:
        await unregister(websocket)

# asyncioイベントループでサーバーを起動
start_server = websockets.serve(video_stream, "0.0.0.0", 5000)

if __name__ == "__main__":
    recording_thread = threading.Thread(target=video_recorder)
    recording_thread.start()
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    recording = False
    recording_thread.join()
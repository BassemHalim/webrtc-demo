import argparse
import asyncio
import cv2

"""
aiortc causes a deadlock when calling cv2.imshow on linux Need to create a named window before
importing aiortc
"""
cv2.namedWindow("ball", cv2.WINDOW_NORMAL)
import numpy as np
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
from aiortc.contrib.signaling import BYE, TcpSocketSignaling
from av import VideoFrame
import multiprocessing as mp


def find_ball(frames_queue: mp.Queue, x: mp.Value, y: mp.Value, event: mp.Event):
    """
    process function that finds ball center in image and return the location in a multiprocessing.Value
    """
    try:
        while True:
            if event.is_set():
                break
            if not frames_queue.empty():
                img = frames_queue.get()

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                circles = cv2.HoughCircles(
                    gray,
                    cv2.HOUGH_GRADIENT,
                    1,
                    20,
                    param1=60,
                    param2=20,
                    minRadius=0,
                    maxRadius=0,
                )
                ball_x = int(circles[0][0][0])
                ball_y = int(circles[0][0][1])
                with x.get_lock():
                    x.value = ball_x
                    y.value = ball_y
    except KeyboardInterrupt:
        pass


def send_coords(channel, x, y, timestamp):
    """
    send the estimated ball position to server through channel
    """
    msg = f"{timestamp},{x},{y}"
    if channel.readyState == "open":
        channel.send(msg)


async def add_dataChannel(pc, signaling):
    """
    renegotiate with server to add a datachannel
    """
    newOffer = await pc.createOffer()
    await pc.setLocalDescription(newOffer)
    await signaling.send(pc.localDescription)


async def run(pc, recorder, signaling):
    # connect signaling
    await signaling.connect()
    # create datachannel to send estimated ball location
    coord_channel = None

    @pc.on("track")
    async def on_track(track):
        """
        if received track is a media track display it and find ball center
        """
        if track.kind == "video":
            if recorder:
                recorder.addTrack(track)
            frames_queue = mp.Queue()
            x, y = mp.Value("i", -1, lock=True), mp.Value("i", -1)
            stopEvent = mp.Event()
            process_a = mp.Process(
                target=find_ball, args=(frames_queue, x, y, stopEvent)
            )
            process_a.start()
            await process_stream(track, frames_queue, x, y)
            stopEvent.set()
            process_a.join()

    async def process_stream(track, frames, x, y):
        """
        continously get frame from stream and display it using opencv and add it to process queue
        """
        nonlocal coord_channel
        while True:
            try:
                frame = await track.recv()
            except Exception:
                cv2.destroyWindow("ball")
                break
            img = frame.to_ndarray(format="rgb24")
            frames.put(img)
            cv2.imshow("ball", img)
            # send coords to server
            # create datachannel to server
            if not coord_channel:
                coord_channel = pc.createDataChannel("chat")
                await add_dataChannel(pc, signaling)
            send_coords(coord_channel, x.value, y.value, frame.pts)

            if cv2.waitKey(1) == 27:
                cv2.destroyWindow("ball")
                break

    # consume signaling
    while True:
        try:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                await recorder.start()

                if obj.type == "offer":
                    # send answer
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)
                    await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is BYE:
                print("Exiting")
                return
        except Exception as e:
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Signaling host (tcp-socket only)"
    )
    parser.add_argument(
        "--signaling-port", default=8080, help="Signaling port (tcp-socket only)"
    )
    args = parser.parse_args()

    # create signaling and peer connection
    signaling = TcpSocketSignaling(host=args.signaling_host, port=args.signaling_port)
    pc = RTCPeerConnection()

    # create media sink
    if args.record_to:
        recorder = MediaRecorder(args.record_to)
    else:
        recorder = MediaBlackhole()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                recorder=recorder,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(recorder.stop())
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())

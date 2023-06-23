import argparse
import asyncio
import cv2
import numpy as np
from av import VideoFrame

from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
)
from aiortc.contrib.signaling import BYE, TcpSocketSignaling
import math


class BallVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an endless stream of a bouncing ball.
    """

    def __init__(self, height=480, width=640, ballRadius=20):
        super().__init__()  # don't forget this!
        self.counter = 0
        self.height, self.width = height, width
        self.ball_radius = ballRadius
        self.ball_color = (0, 150, 255)
        self.x, self.y = self.width // 2, self.height // 2
        self.dx, self.dy = 3, 2
        self.ballCenters = {}  # timestamp : (x, y)

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame, center = self.__gen_next_frame()
        frame.pts = pts
        frame.time_base = time_base
        self.ballCenters[frame.pts] = center
        self.counter += 1
        return frame

    def __gen_next_frame(self):
        """
        determine the ball's next position and return a frame with that postion
        """
        frame = self.__create_frame(self.x, self.y)
        center = (self.x, self.y)
        self.x += self.dx
        self.y += self.dy
        if self.x <= self.ball_radius or self.x >= (self.width - self.ball_radius):
            self.dx *= -1
        if self.y <= self.ball_radius or self.y >= (self.height - self.ball_radius):
            self.dy *= -1
        return VideoFrame.from_ndarray(frame),center

    def __create_frame(self, x, y):
        """
        create a frame with a ball centered at (x,y)
        """
        background = np.zeros((self.height, self.width, 3), np.uint8)
        return cv2.circle(background, (x, y), self.ball_radius, self.ball_color, -1)

    def compute_coord_error(self, timestamp, estimated_x, estimated_y):
        """
        computes distance difference between estimated and true ball position
        returns the true postion and the distance difference
        """
        x, y = self.ballCenters[timestamp]
        diff = math.dist([estimated_x, estimated_y], [x, y])
        del self.ballCenters[timestamp]
        return (x, y), diff


async def consume_signaling(pc, signaling):
    """
    handle any signaling received
    """
    # consume signaling
    while True:
        try:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)

                if obj.type == "offer":
                    # send answer
                    print("received offer")
                    await pc.setLocalDescription(await pc.createAnswer())
                    await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is BYE:
                print("Exiting")
                return
        except Exception:
            return


async def run(pc, signaling):
    @pc.on("datachannel")
    def on_datachannel(channel):
        """
        process received data from datachannel
        """

        @channel.on("message")
        def on_message(message):
            if isinstance(message, str):
                timestamp, est_x, est_y = message.split(",")
                actual, error = BallStream.compute_coord_error(
                    float(timestamp), int(est_x), int(est_y)
                )
                print(
                    f"Actual: {actual} Estimate: ({est_x},{est_y}) error: {error:2.3f} pixels"
                )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        if pc.connectionState == "failed":
            await pc.close()

    # connect signaling
    await signaling.connect()
    BallStream = BallVideoStreamTrack()

    # send offer
    pc.addTrack(BallStream)
    await pc.setLocalDescription(await pc.createOffer())
    await signaling.send(pc.localDescription)
    await consume_signaling(pc, signaling)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video stream from the command line")
    parser.add_argument(
        "--signaling-host", default="127.0.0.1", help="Signaling host (tcp-socket only)"
    )
    parser.add_argument(
        "--signaling-port", default=8080, help="Signaling port (tcp-socket only)"
    )
    args = parser.parse_args()

    # create TCP socket and peer connection
    signaling = TcpSocketSignaling(host=args.signaling_host, port=args.signaling_port)
    pc = RTCPeerConnection()

    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())

## WebRTC video Streaming and Position Estimation
__By: Bassem Halim__

This project demonstrates a simple implementation of a WebRTC-based video streaming and position estimation system using a server and client application.

## Overview

The server application (server.py) opens a WebRTC video stream of a bouncing ball. It generates frames with a ball animation and streams them to connected clients. 

The client application (client.py) receives the video stream from the server and displays it. It then spawns a new process that estimates the position of the bouncing ball in each frame using computer vision techniques. The client then opens a data channel to the server and sends the estimated positions back through that channel

The server then computes and displays the error between the actual and the estimated ball positions

the webRTC logic was handled by the library "aiortc" and a TCPsocket was used for signaling

I tested 2 techniques to determine the ball position; the first was to to get the sum of each row/column and find the index of the max sum (argmax).
The second was using openCV Hough transform to find the centers. Both solutions had similar results however I opted for the openCV solution because the other solution assumes the ball is placed on a black background which would otherwise not find the correct solution. 
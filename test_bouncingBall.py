from server import BallVideoStreamTrack
import pytest

@pytest.mark.asyncio
async def test_FrameDimension():
    ballStream = BallVideoStreamTrack(200, 200)
    frame =  await ballStream.recv()
    img = frame.to_ndarray(format="rgb24")
    assert (img.shape == (200, 200, 3))

@pytest.mark.asyncio
async def test_compute_coord_error():
    ballStream = BallVideoStreamTrack(200, 200)
    frame =  await ballStream.recv()
    img = frame.to_ndarray(format="rgb24")
    assert (img.shape == (200, 200, 3))
    
    x_ini, y_ini = 100, 100
    (tru_x, tru_y), error = ballStream.compute_coord_error(frame.pts, x_ini, y_ini)
    assert (error == 0)
    assert (tru_x == x_ini)
    assert (tru_y == y_ini)
    
@pytest.mark.asyncio
async def test_LongStream():
    ballStream = BallVideoStreamTrack(200, 200)
    for _ in range(200):
        frame =  await ballStream.recv()
        img = frame.to_ndarray(format="rgb24")
        assert (img.shape == (200, 200, 3))
"""Run this on the Raspberry Pi with:

    sudo fastapi run leds-web.py

Run on laptop:

    python -m http.server

(A page on localhost can access media even without HTTPS.)
"""

from pydantic import BaseModel
from rpi_ws281x import PixelStrip, Color
import asyncio
import fastapi
import fastapi.staticfiles
import json
import time

LED_COUNT = 600
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(
    LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
)
strip.begin()
app = fastapi.FastAPI()

last_ws_data_timestamp = 0


@app.get("/")
async def get():
    return fastapi.responses.RedirectResponse("/static/music.html")


async def idle():
    j = 0
    while True:
        if time.time() - last_ws_data_timestamp > 1:
            for i in range(LED_COUNT):
                strip.setPixelColor(
                    i, Color(0, 0, 0) if i != j else Color(255, 255, 255)
                )
            j = (j + 1) % LED_COUNT
        asyncio.sleep(0.1)


idle()


@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    global last_ws_data_timestamp
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data = json.loads(data)
        last_ws_data_timestamp = time.time()
        for i, (r, g, b) in enumerate(data):
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()

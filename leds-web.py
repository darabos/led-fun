'''Run this on the Raspberry Pi with:

    sudo fastapi run leds-web.py

Run on laptop:

    python -m http.server

(A page on localhost can access media even without HTTPS.)
'''
from rpi_ws281x import PixelStrip, Color
import fastapi
import fastapi.staticfiles
import time
from pydantic import BaseModel
import json

LED_COUNT = 600
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
app = fastapi.FastAPI()

@app.get("/")
async def get():
    return fastapi.responses.RedirectResponse("/static/music.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data = json.loads(data)
        for i, (r,g,b) in enumerate(data):
            strip.setPixelColor(i, Color(r,g,b))
        strip.show()

"""Run this on the Raspberry Pi with:

    sudo fastapi run leds-web.py

Run on laptop:

    python -m http.server

(A page on localhost can access media even without HTTPS.)
"""

import contextlib
from math import sin, pi, copysign
import random
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


@contextlib.asynccontextmanager
async def lifespan(app):
    asyncio.create_task(idle())
    yield


app = fastapi.FastAPI(lifespan=lifespan)

last_ws_data_timestamp = 0


@app.get("/")
async def get():
    return fastapi.responses.RedirectResponse("/static/music.html")


MODES = [
    # "test",
    "xmas static",
    "xmas switching",
    "xmas left",
    "xmas cross",
    "xmas right",
    "xmas momentum",
    "xmas blend",
    "xmas fountain",
    "inigo",
    "starry night",
]


def i2b(i):
    return min(255, max(0, int(i)))


PERM = list(range(LED_COUNT))
random.shuffle(PERM)


def get_color(t, m, i):
    r = g = b = 0
    if m == "test":
        if i == abs(t % (2 * LED_COUNT) - LED_COUNT):
            g = 1
    elif m == "xmas static":
        if i % 10 == 0:
            r = 255
        elif i % 10 == 5:
            g = 255
    elif m == "xmas switching":
        if (i + 5 * (t // 10)) % 10 == 0:
            r = 255
        elif (i + 5 * (t // 10)) % 10 == 5:
            g = 255
    elif m == "xmas left":
        if (i + t) % 10 == 0:
            r = 255
        elif (i + t) % 10 == 5:
            g = 255
    elif m == "xmas momentum":
        p = int(i + 200 * sin(t / 100))
        if p % 10 == 0:
            r = 255
        elif p % 10 == 5:
            g = 255
    elif m == "xmas cross":
        if (i - t) % 10 == 0:
            r = 255
        elif (i + t) % 10 == 5:
            g = 255
    elif m == "xmas right":
        if (i - t) % 10 == 0:
            r = 255
        elif (i - t) % 10 == 5:
            g = 255
    elif m == "xmas right":
        if (i - t) % 10 == 0:
            r = 255
        elif (i - t) % 10 == 5:
            g = 255
    elif m == "xmas blend":
        p = i + 200 * sin(t / 100)
        r = max(0, sin(p / 10)) ** 2 * 255
        p = i + 300 * sin(t / 130)
        g = max(0, sin(p / 10)) ** 2 * 255
    elif m == "xmas fountain":
        p = (abs(i - 311) - t) / 20
        r = max(0, sin(p)) ** 3 * 600 - 200 + copysign(100, sin(p / 2))
        g = max(0, sin(p)) ** 3 * 600 - 200 + copysign(100, sin(p / 2 + pi))
        b = max(0, sin(p)) ** 3 * 600 - 400
    elif m == "starry night":
        j = PERM[i]
        r = sin(t / (2000 + j * 10) + j * 20) ** 10000 * 255
        g = r
        b = max(1, r)
    elif m == "inigo":
        # https://www.youtube.com/watch?v=TH3OTy5fTog
        p = t / 100
        A = [0.1 + 0.1 * sin(1 * (rgb + p)) for rgb in range(3)]
        B = [0.1 + 0.01 * sin(2 * (rgb + p)) for rgb in range(3)]
        C = [0.5 + 0.1 * sin(3 * (rgb + p)) for rgb in range(3)]
        D = [0.5 + 0.1 * sin(5 * (rgb + p)) for rgb in range(3)]
        j = i / 100
        [r, g, b] = [
            255 * (A[rgb] + B[rgb] * sin(2 * pi * (C[rgb] * j + D[rgb])))
            for rgb in range(3)
        ]
    return r, g, b


async def idle():
    t = 0
    mode = 0
    MODE_PERIOD = LED_COUNT * 6
    while True:
        if time.time() - last_ws_data_timestamp > 2:
            m = MODES[mode]
            for i in range(LED_COUNT):
                r, g, b = get_color(t, m, i)
                if t < 20:
                    r2, g2, b2 = get_color(t + MODE_PERIOD, MODES[mode - 1], i)
                    r = r * t / 20 + r2 * (20 - t) / 20
                    g = g * t / 20 + g2 * (20 - t) / 20
                    b = b * t / 20 + b2 * (20 - t) / 20
                c = Color(i2b(r), i2b(g), i2b(b))
                strip.setPixelColor(i, c)
            strip.show()
            t += 1
            if t == LED_COUNT * 6:
                t = 0
                mode = (mode + 1) % len(MODES)
        await asyncio.sleep(0.01)


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

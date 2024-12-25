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
import rainbow
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
    "flame tennis",
    "inigo",
    "starry night",
    "she ra",
    "flames",
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
    elif m == "she ra":
        p = abs(i - 311) + t * 3
        c = int(p) % len(rainbow.colors)
        r, g, b = rainbow.colors[c]
    elif m == "starry night":
        j = PERM[i]
        r = sin(t / (2000 + j * 10) + j * 20) ** 10000 * 255
        g = r
        b = max(1, r)
    elif m == "flame tennis":
        LIFT = 100
        if LIFT < i < LED_COUNT - LIFT:
            i -= LIFT
            COUNT = LED_COUNT - 2 * LIFT
            v = (i - t * 3) % (2 * COUNT) - (2 * COUNT - 100)
            v *= 3
            r = max(0, v)
            g = max(0, v - 100)
            b = max(0, v - 200)
            v = (-i - t * 3) % (2 * COUNT) - (2 * COUNT - 100)
            v *= 3
            b += max(0, v)
            g += max(0, v - 100)
            r += max(0, v - 200)
    elif m == "flames":
        if 190 <= i <= 433:
            v = 0
            for j in range(5):
                p = int(
                    sin(t / (21 + v)) * 50
                    + sin(t / (23 + v)) * 50
                    + sin(t / (27 + v)) * 50
                    + sin(t / (177 + v)) * 50
                    + 311
                )
                r += 10 if p == i else 0
                t += 1000000
                v += 1
        else:
            if i > 433:
                i = 600 - i
            f = lambda x: max(0, sin(x))  # noqa: E731
            v = f(i / 10 - t / 7) + f(i / 8 - t / 3) + f(i / 20 - t / 17)
            v -= 0.1
            v += max(0, 100 / (i + 1) - 1)
            V = 100
            r = max(0, v * V)
            g = max(0, v * V - 255)
            b = max(0, v * V - 510)
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
    MODE_PERIOD = LED_COUNT * 10
    while True:
        if time.time() - last_ws_data_timestamp > 2:
            m = MODES[mode]
            for i in range(LED_COUNT):
                r, g, b = get_color(t, m, i)
                FADE = 20
                if t < FADE:
                    r2, g2, b2 = get_color(t + MODE_PERIOD, MODES[mode - 1], i)
                    r = r * t / FADE + r2 * (FADE - t) / FADE
                    g = g * t / FADE + g2 * (FADE - t) / FADE
                    b = b * t / FADE + b2 * (FADE - t) / FADE
                c = Color(i2b(r), i2b(g), i2b(b))
                strip.setPixelColor(i, c)
            strip.show()
            t += 1
            if t == MODE_PERIOD:
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

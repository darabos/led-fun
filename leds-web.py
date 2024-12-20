from rpi_ws281x import PixelStrip, Color
import fastapi
import time

LED_COUNT = 600
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
while 0:
    for j in range(LED_COUNT):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 255 if i==j else 0, 0))
        strip.show()
        time.sleep(0.01)


app = fastapi.FastAPI()

from pydantic import BaseModel


class SetColorRequest(BaseModel):
    colors: list[tuple[int, int, int]]

@app.post("/set_colors")
async def set_colors(req: SetColorRequest):
    for i, (r,g,b) in enumerate(req.colors):
        strip.setPixelColor(i, Color(r,g,b))
    strip.show()
    return {"status": "ok"}

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

music_html = """
<!DOCTYPE html>
<html>
  <body>
    <script>
      const ws = new WebSocket(`ws://${location.host}/ws`);
      let analyser;
      let dataArray;
      async function run() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);
        source.connect(analyser);
      }

      let colors = [];
      setInterval(() => {
        if (!analyser) {
          return;
        }
        analyser.getByteTimeDomainData(dataArray);
        let total = 0;
        for (let i = 0; i < dataArray.length; ++i) {
          total += Math.abs(dataArray[i] - 128);
        }
        analyser.getByteFrequencyData(dataArray);
        let totalFreq = 0;
        for (let i = 0; i < dataArray.length; ++i) {
          totalFreq += i * dataArray[i];
        }
        const freq = totalFreq / dataArray.length / dataArray.length;
        const v = total / 100;
        for (let i = 0; i < 2; ++i) {
          colors.unshift([(freq * v) / 1, 9 + (v * v) / 100, v - 100]);
        }
        colors = colors.slice(0, 600);
        if (ws.readyState === 1) {
          const f = x => Math.min(10, Math.max(0, Math.floor(x / 10)));
          ws.send(JSON.stringify(colors.map(([r, g, b]) => [f(r), f(g), f(b)])));
        }
      }, 30);
      run();
    </script>
  </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(music_html)

import json

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data = json.loads(data)
        for i, (r,g,b) in enumerate(data):
            strip.setPixelColor(i, Color(r,g,b))
        strip.show()
#        await websocket.send_text(f"Message text was: {data}")

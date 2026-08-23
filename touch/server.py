#!/usr/bin/env python3
"""小黑猫 touch server — receives ESP32 sensor data, serves live visualization."""

import json, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9333
latest = {"ts": 0, "data": {}}
lock = threading.Lock()

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>kuroneko</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#eee;font-family:system-ui;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh}
h1{font-size:1.2rem;margin-bottom:1.5rem;opacity:.6}
.cat{position:relative;width:280px;height:360px}
.zone{position:absolute;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.7rem;opacity:.3;transition:opacity .15s,background .15s}
.zone.active{opacity:1}
#hd{width:80px;height:70px;top:0;left:100px;border-radius:45%}
#el{width:40px;height:50px;top:-10px;left:70px;border-radius:40% 40% 50% 50%;transform:rotate(-15deg)}
#er{width:40px;height:50px;top:-10px;left:170px;border-radius:40% 40% 50% 50%;transform:rotate(15deg)}
#bd{width:120px;height:160px;top:80px;left:80px;border-radius:50% 50% 45% 45%}
#fl{width:45px;height:80px;top:200px;left:65px;border-radius:40%}
#fr{width:45px;height:80px;top:200px;left:170px;border-radius:40%}
#bl{width:45px;height:80px;top:270px;left:75px;border-radius:40%}
#br{width:45px;height:80px;top:270px;left:160px;border-radius:40%}
.status{margin-top:2rem;font-size:.8rem;opacity:.4}
</style></head><body>
<h1>kuroneko</h1>
<div class="cat">
 <div class="zone" id="el">ear L</div>
 <div class="zone" id="er">ear R</div>
 <div class="zone" id="hd">head</div>
 <div class="zone" id="bd">body</div>
 <div class="zone" id="fl">front L</div>
 <div class="zone" id="fr">front R</div>
 <div class="zone" id="bl">back L</div>
 <div class="zone" id="br">back R</div>
</div>
<div class="status" id="st">waiting...</div>
<script>
const T=150;
function poll(){
 fetch("/data").then(r=>r.json()).then(d=>{
  if(!d.data||!Object.keys(d.data).length){document.getElementById("st").textContent="waiting...";return}
  let ago=((Date.now()/1000)-d.ts).toFixed(0);
  document.getElementById("st").textContent=ago<5?"live":"last: "+ago+"s ago";
  for(let[k,v]of Object.entries(d.data)){
   let el=document.getElementById(k);if(!el)continue;
   let on=v>T;
   el.classList.toggle("active",on);
   let h=on?Math.min(200+v/10,360):0;
   el.style.background=on?"hsl("+h+",80%,55%)":"rgba(255,255,255,.08)";
  }
 }).catch(()=>{}).finally(()=>setTimeout(poll,200));
}
poll();
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/data":
            with lock:
                body = json.dumps(latest).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE.encode())

    def do_POST(self):
        if self.path == "/hello":
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n)
            try:
                data = json.loads(raw)
                with lock:
                    latest["ts"] = time.time()
                    latest["data"] = data
            except Exception:
                pass
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    s = HTTPServer(("0.0.0.0", PORT), H)
    print(f"kuroneko touch server on :{PORT}")
    s.serve_forever()

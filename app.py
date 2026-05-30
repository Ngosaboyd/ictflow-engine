import asyncio
import json
import os
import threading
from flask import Flask, jsonify
import websockets

app = Flask(__name__)

# Core algorithmic memory blocks
candles = []
active_signals = []


def calculate_ict_signals(data):
    """Hard-coded mechanical execution algorithm targeting Volatility 75 structural shifts"""
    global active_signals
    if len(data) < 25:
        return
    try:
        # 1. Isolate historical liquidity pools
        historical_highs = [float(c["high"]) for c in data[-25:-5]]
        historical_lows = [float(c["low"]) for c in data[-25:-5]]
        highest_high = max(historical_highs)
        lowest_low = min(historical_lows)

        c1 = {k: float(v) for k, v in data[-3].items() if k != "epoch"}
        c2 = {k: float(v) for k, v in data[-2].items() if k != "epoch"}
        c3 = {k: float(v) for k, v in data[-1].items() if k != "epoch"}

        # --- BULLISH ALGORITHMIC ALIGNMENT (DISCOUNT BUYING) ---
        is_bullish_sweep = any(
            float(c["low"]) <= lowest_low for c in data[-3:]
        )
        recent_minor_high = max(float(c["high"]) for c in data[-5:-2])
        has_bullish_mss = c3["close"] > recent_minor_high
        has_bullish_fvg = c3["low"] > c1["high"]

        if has_bullish_fvg and (is_bullish_sweep or has_bullish_mss):
            entry = c3["low"]
            sl = min(c1["low"], c2["low"], c3["low"]) - 50.0

            local_low = min(float(c["low"]) for c in data[-10:])
            local_high = max(float(c["high"]) for c in data[-10:])
            equilibrium = (local_high + local_low) / 2

            if entry <= equilibrium:  # Discount validation rule
                tp = entry + ((entry - sl) * 3.0)  # Pure 1:3 mathematical edge
                new_signal = {
                    "asset": "Volatility 75 Index",
                    "type": "BUY LIMIT",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "lot": 0.005,
                    "rr": "1:3",
                    "status": "VALID",
                }
                if not any(
                    s["entry"] == new_signal["entry"] for s in active_signals
                ):
                    active_signals.append(new_signal)

        # --- BEARISH ALGORITHMIC ALIGNMENT (PREMIUM SELLING) ---
        is_bearish_sweep = any(
            float(c["high"]) >= highest_high for c in data[-3:]
        )
        recent_minor_low = min(float(c["low"]) for c in data[-5:-2])
        has_bearish_mss = c3["close"] < recent_minor_low
        has_bearish_fvg = c3["high"] < c1["low"]

        if has_bearish_fvg and (is_bearish_sweep or has_bearish_mss):
            entry = c3["high"]
            sl = max(c1["high"], c2["high"], c3["high"]) + 50.0

            local_low = min(float(c["low"]) for c in data[-10:])
            local_high = max(float(c["high"]) for c in data[-10:])
            equilibrium = (local_high + local_low) / 2

            if entry >= equilibrium:  # Premium validation rule
                tp = entry - ((sl - entry) * 3.0)
                new_signal = {
                    "asset": "Volatility 75 Index",
                    "type": "SELL LIMIT",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "lot": 0.005,
                    "rr": "1:3",
                    "status": "VALID",
                }
                if not any(
                    s["entry"] == new_signal["entry"] for s in active_signals
                ):
                    active_signals.append(new_signal)
    except Exception as e:
        print(f"Algorithm parsing variation anomaly: {e}")


async def stream_deriv_data():
    global candles
    url = "wss://ws.binaryws.com/websockets/v3?app_id=36544&l=EN&brand=deriv"
    while True:
        try:
            async with websockets.connect(
                url, ping_interval=20, ping_timeout=20
            ) as ws:
                req = {
                    "ticks_history": "R_75",
                    "adjust_start_time": 1,
                    "count": 100,
                    "end": "latest",
                    "granularity": 900,
                    "style": "candles",
                    "subscribe": 1,
                }
                await ws.send(json.dumps(req))
                async for message in ws:
                    msg = json.loads(message)
                    if "candles" in msg:
                        candles = msg["candles"]
                    elif "ohlc" in msg:
                        ohlc_data = msg["ohlc"]
                        new_candle = {
                            "open": float(ohlc_data["open"]),
                            "high": float(ohlc_data["high"]),
                            "low": float(ohlc_data["low"]),
                            "close": float(ohlc_data["close"]),
                            "epoch": int(ohlc_data["open_time"]),
                        }
                        if (
                            len(candles) > 0
                            and candles[-1].get("epoch") == new_candle["epoch"]
                        ):
                            candles[-1] = new_candle
                        else:
                            candles.append(new_candle)
                        if len(candles) > 150:
                            candles.pop(0)
                        calculate_ict_signals(candles)
        except Exception:
            await asyncio.sleep(5)


def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stream_deriv_data())


@app.route("/api/signals", methods=["GET"])
def get_signals():
    response = jsonify(active_signals)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ICTFLOW Cloud Matrix</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen">
        <header class="border-b border-slate-900 bg-slate-900/50 backdrop-blur sticky top-0 z-50 px-4 py-4 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <div class="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse"></div>
                <span class="font-black text-xl tracking-wider text-slate-100">ICTFLOW CLOUD</span>
            </div>
            <div id="status" class="text-[10px] font-bold px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">CLOUD DEPLOYMENT ACTIVE</div>
        </header>

        <main class="max-w-xl mx-auto px-4 py-6">
            <div class="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-5 mb-6 shadow-xl">
                <span class="text-[10px] text-cyan-400 tracking-widest uppercase font-bold">24/7 RADAR METRICS</span>
                <h1 class="text-xl font-black text-slate-100 mt-0.5">Volatility 75 Index (M15)</h1>
                <p class="text-xs text-slate-400 mt-2 leading-relaxed">Cloud server monitoring institutional data packets directly from the Deriv framework pipeline.</p>
            </div>

            <h2 class="text-xs font-bold text-slate-500 tracking-wider uppercase mb-3">Verified Institutional Setups</h2>
            <div id="signals-container" class="space-y-4">
                <div class="py-12 border border-dashed border-slate-800 rounded-2xl text-center bg-slate-900/20">
                    <p class="text-xs font-bold text-emerald-400 tracking-widest animate-pulse">ALGO RUNNING - SCANNING MATRIX...</p>
                </div>
            </div>
        </main>

        <script>
            async function fetchSignals() {
                try {
                    const res = await fetch('/api/signals');
                    const data = await res.json();
                    const container = document.getElementById('signals-container');
                    
                    if (data.length === 0) {
                        container.innerHTML = `
                            <div class="py-12 border border-dashed border-slate-800 rounded-2xl text-center bg-slate-900/20">
                                <p class="text-xs font-bold text-emerald-400 tracking-widest animate-pulse">ALGO RUNNING - SCANNING MATRIX...</p>
                                <p class="text-[10px] text-slate-500 mt-1">Awaiting high-probability liquidity sweep footprint verification</p>
                            </div>`;
                        return;
                    }
                    
                    container.innerHTML = data.map(sig => `
                        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md">
                            <div class="flex justify-between items-center border-b border-slate-800 pb-2 mb-3">
                                <div>
                                    <h3 class="font-bold text-sm text-slate-200">\${sig.asset}</h3>
                                    <span class="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Target Matrix Edge: \${sig.rr}</span>
                                </div>
                                <span class="px-2.5 py-0.5 rounded text-[10px] font-black tracking-wider \${sig.type.includes('BUY') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}\">\text{\${sig.type}}</span>
                            </div>
                            <div class="grid grid-cols-3 gap-2">
                                <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-900/50 text-center">
                                    <span class="block text-[9px] text-slate-500 font-bold uppercase">ENTRY</span>
                                    <span class="font-mono text-xs font-bold text-slate-300">\${sig.entry}</span>
                                </div>
                                <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-900/50 text-center">
                                    <span class="block text-[9px] text-rose-400 font-bold uppercase">STOP LOSS</span>
                                    <span class="font-mono text-xs font-bold text-rose-400">\${sig.sl}</span>
                                </div>
                                <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-900/50 text-center">
                                    <span class="block text-[9px] text-emerald-400 font-bold uppercase">TAKE PROFIT</span>
                                    <span class="font-mono text-xs font-bold text-emerald-400">\${sig.tp}</span>
                                </div>
                            </div>
                        </div>
                    `).join('');
                } catch (e) {
                    document.getElementById('status').innerText = "CONNECTION DESYNCED";
                    document.getElementById('status').className = "text-[10px] font-bold px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20";
                }
            }
            setInterval(fetchSignals, 4000);
            fetchSignals();
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    t = threading.Thread(target=start_async_loop)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

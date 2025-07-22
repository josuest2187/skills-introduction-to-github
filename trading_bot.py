import pandas as pd
import pandas_ta as ta
import time
import schedule
import threading
import tkinter as tk
from tkinter import messagebox
import requests
from binance.client import Client
from binance.enums import *
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import math
from datetime import datetime

# ============================
# ✅ DATOS DE ACCESO BINANCE
# ============================
API_KEY = 'kWHiHQjuneLNAvVyHp5A4SqFhkCzGdHdX83AxrfKSHtOIWsdRnzmkkvPHEnQZwzQ'
API_SECRET = 'XKC40qPdNnGuYIlWnU1euu9hhT7U4LNTUhyzvLROwHnBIi07NXJTO9AEUeKyXJTs'
client = Client(API_KEY, API_SECRET)
client.API_URL = 'https://api.binance.com/api'

# Sincronizar el reloj del cliente con el del servidor
server_time = client.get_server_time()
local_time = int(time.time() * 1000)
client.timestamp_offset = server_time['serverTime'] - local_time

# ============================
# ✅ DATOS DE TELEGRAM
# ============================
TELEGRAM_TOKEN = '7777582620:AAH5fQWvSxx_ZkEelrDhTcf8Tq2bxWRYz9U'
TELEGRAM_CHAT_ID = '5637585144'

# ============================
# ⚙️ CONFIGURACIÓN DEL BOT
# ============================
SYMBOL = ''
TIMEFRAMES = ['15m', '1h', '4h']
LIMIT = 150
RISK_PERCENTAGE = 10
TP_PERCENTAGE = 2
SL_PERCENTAGE = 1

# ============================
# 📋 VARIABLES PARA HISTORIAL Y ESTADÍSTICAS
# ============================
trade_history = []
wins = 0
losses = 0

# ============================
# ✅ ENVIAR MENSAJE A TELEGRAM
# ============================
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Error al enviar mensaje a Telegram:", e)

# ============================
# ✅ OBTENER DATOS DE BINANCE
# ============================
def get_klines(symbol, interval, limit=150):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                           'close_time', 'quote_asset_volume', 'number_of_trades',
                                           'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        return df
    except:
        return None

# ============================
# 📈 INDICADORES TÉCNICOS
# ============================
def apply_indicators(df):
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=100, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True)
    df.ta.bbands(append=True)
    df.ta.adx(append=True)

    df.rename(columns={
        'EMA_20': 'ema20',
        'EMA_50': 'ema50',
        'EMA_100': 'ema100',
        'RSI_14': 'rsi',
        'MACD_12_26_9': 'macd',
        'BBU_20_2.0': 'bb_upper',
        'BBL_20_2.0': 'bb_lower',
        'ADX_14': 'adx'
    }, inplace=True)
    return df

# ============================
# 🤖 IA: FILTRO CON RANDOM FOREST
# ============================
def train_model(df):
    df = df.dropna()
    X = df[['ema20', 'ema50', 'ema100', 'rsi', 'macd', 'adx']]
    y = np.where(df['close'].shift(-1) > df['close'], 1, 0)
    model = RandomForestClassifier()
    model.fit(X[:-1], y[:-1])
    return model

def predict_signal(df, model):
    X_latest = df[['ema20', 'ema50', 'ema100', 'rsi', 'macd', 'adx']].iloc[-1:]
    prediction = model.predict(X_latest)[0]
    return 'BUY' if prediction == 1 else 'SELL'

# ============================
# 💸 GESTIÓN DE CAPITAL Y ORDENES
# ============================

def get_balance():
    balance = client.get_asset_balance(asset='USDT')
    return float(balance['free'])

def get_step_size(symbol):
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    return float(f['stepSize'])
    return 0.000001  # Valor por defecto si no encuentra

def round_step_size(quantity, step_size):
    return math.floor(quantity / step_size) * step_size

def place_order(symbol, signal):
    try:
        # Validar símbolo
        exchange_info = client.get_exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols']]
        if symbol not in symbols:
            raise Exception(f"❌ El símbolo {symbol} no es válido o no está disponible en tu cuenta.")

        # Obtener balance y precio
        balance = get_balance()
        price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        amount_to_use = balance * (RISK_PERCENTAGE / 100)
        quantity = amount_to_use / price

        step_size = get_step_size(symbol)

        # Impresiones para depurar
        print(f"Balance USDT: {balance}")
        print(f"Amount to use (risk %): {amount_to_use}")
        print(f"Precio actual {symbol}: {price}")
        print(f"Cantidad antes de ajustar step size: {quantity}")
        print(f"Step size para {symbol}: {step_size}")

        quantity = round_step_size(quantity, step_size)

        if quantity < step_size or quantity <= 0:
            raise Exception(f"❌ La cantidad calculada es menor que el mínimo permitido ({step_size}). Revisa balance o porcentaje de riesgo.")

        decimals = abs(int(round(np.log10(step_size))))
        quantity_str = f"{quantity:.{decimals}f}"

        if signal == 'BUY':
            order = client.order_market_buy(symbol=symbol, quantity=quantity_str)
            tp_price = round(price * (1 + TP_PERCENTAGE / 100), 2)
            sl_price = round(price * (1 - SL_PERCENTAGE / 100), 2)
        elif signal == 'SELL':
            order = client.order_market_sell(symbol=symbol, quantity=quantity_str)
            tp_price = round(price * (1 - TP_PERCENTAGE / 100), 2)
            sl_price = round(price * (1 + SL_PERCENTAGE / 100), 2)
        else:
            raise Exception("❌ Señal inválida. Debe ser 'BUY' o 'SELL'.")

        mensaje = f"✅ Orden {signal} ejecutada en {symbol}. TP: {tp_price}, SL: {sl_price}"
        print(mensaje)
        send_telegram_message(mensaje)

    except Exception as e:
        error_msg = f"❌ Error al colocar orden en {symbol}: {str(e)}"
        print(error_msg)
        send_telegram_message(error_msg)

# ============================
# 📊 ANÁLISIS Y ACCIÓN (con historial y simulación resultado)
# ============================
def analyze(symbol):
    global wins, losses
    df = get_klines(symbol, '15m', LIMIT)
    if df is None:
        return "Error al obtener datos."

    df = apply_indicators(df)
    model = train_model(df)
    signal = predict_signal(df, model)

    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    tp_price = round(price * (1 + TP_PERCENTAGE / 100), 2) if signal == 'BUY' else round(price * (1 - TP_PERCENTAGE / 100), 2)
    sl_price = round(price * (1 - SL_PERCENTAGE / 100), 2) if signal == 'BUY' else round(price * (1 + SL_PERCENTAGE / 100), 2)

    # Simular resultado (puedes mejorar esto con datos en vivo)
    simulated_close = df['close'].iloc[-1]
    if signal == 'BUY':
        result = 'GANADA' if simulated_close >= tp_price else 'PERDIDA'
    else:
        result = 'GANADA' if simulated_close <= tp_price else 'PERDIDA'

    if result == 'GANADA':
        wins += 1
    else:
        losses += 1

    total_trades = wins + losses
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    # Guardar en historial
    trade_history.append({
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'symbol': symbol,
        'signal': signal,
        'entry': price,
        'tp': tp_price,
        'sl': sl_price,
        'resultado': result
    })

    # Ejecutar orden real
    place_order(symbol, signal)

    return f"Señal para {symbol}: {signal} | Resultado: {result} | Aciertos: {win_rate:.2f}%"

# ============================
# 🖥️ MOSTRAR HISTORIAL EN LA GUI
# ============================
def mostrar_historial():
    historial_text.delete('1.0', tk.END)
    for trade in trade_history[-10:]:  # Mostrar últimas 10 operaciones
        linea = f"[{trade['fecha']}] {trade['symbol']} - {trade['signal']} @ {trade['entry']} → TP: {trade['tp']} / SL: {trade['sl']} → {trade['resultado']}\n"
        historial_text.insert(tk.END, linea)

    total = wins + losses
    if total > 0:
        aciertos = (wins / total) * 100
        historial_text.insert(tk.END, f"\n✅ Aciertos: {wins} | ❌ Fallos: {losses} | 🎯 Efectividad: {aciertos:.2f}%\n")

# ============================
# 💻 INTERFAZ GRÁFICA (GUI)
# ============================
window = tk.Tk()
window.title("BOT DE TRADING")
window.geometry("450x650")
window.configure(bg="#1e1e1e")

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
symbol_var = tk.StringVar(window)
symbol_var.set(symbols[0])

symbol_menu = tk.OptionMenu(window, symbol_var, *symbols)
symbol_menu.pack(pady=5)

risk_label = tk.Label(window, text="Riesgo %", fg="white", bg="#1e1e1e")
risk_label.pack()
risk_entry = tk.Entry(window)
risk_entry.insert(0, str(RISK_PERCENTAGE))
risk_entry.pack()

tp_label = tk.Label(window, text="Take Profit %", fg="white", bg="#1e1e1e")
tp_label.pack()
tp_entry = tk.Entry(window)
tp_entry.insert(0, str(TP_PERCENTAGE))
tp_entry.pack()

sl_label = tk.Label(window, text="Stop Loss %", fg="white", bg="#1e1e1e")
sl_label.pack()
sl_entry = tk.Entry(window)
sl_entry.insert(0, str(SL_PERCENTAGE))
sl_entry.pack()

output_text = tk.Text(window, height=10, width=50, bg="black", fg="lime")
output_text.pack(pady=10)

def start():
    global RISK_PERCENTAGE, TP_PERCENTAGE, SL_PERCENTAGE, SYMBOL
    SYMBOL = symbol_var.get()
    RISK_PERCENTAGE = float(risk_entry.get())
    TP_PERCENTAGE = float(tp_entry.get())
    SL_PERCENTAGE = float(sl_entry.get())

    result = analyze(SYMBOL)
    output_text.insert(tk.END, result + "\n")
    send_telegram_message(result)
    mostrar_historial()

btn = tk.Button(window, text="INICIAR", command=start, bg="green", fg="white")
btn.pack(pady=10)

historial_text = tk.Text(window, height=12, width=60, bg="#222", fg="white")
historial_text.pack(pady=5)

window.mainloop()
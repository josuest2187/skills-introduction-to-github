import pandas as pd
import pandas_ta as ta
import time
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import Font
import requests
from binance.client import Client
from binance.enums import *
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np
import math
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")

# ============================
# 🔧 CONFIGURACIÓN Y LOGGING
# ============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Clase para manejar la configuración del bot"""
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        default_config = {
            "binance": {
                "api_key": "",
                "api_secret": "",
                "testnet": True
            },
            "telegram": {
                "token": "",
                "chat_id": ""
            },
            "trading": {
                "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT"],
                "timeframes": ["15m", "1h", "4h"],
                "limit": 200,
                "risk_percentage": 5,
                "tp_percentage": 3,
                "sl_percentage": 2,
                "min_balance": 10,
                "max_trades_per_day": 5
            },
            "ml": {
                "model_type": "RandomForest",
                "n_estimators": 100,
                "test_size": 0.2,
                "min_accuracy": 0.6
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("✅ Configuración cargada desde archivo")
            except Exception as e:
                logger.error(f"❌ Error al cargar configuración: {e}")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Guardar configuración en archivo JSON"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("✅ Configuración guardada")
        except Exception as e:
            logger.error(f"❌ Error al guardar configuración: {e}")
    
    def get(self, section: str, key: str = None):
        """Obtener valor de configuración"""
        if key:
            return self.config.get(section, {}).get(key)
        return self.config.get(section, {})

class TradingBot:
    """Clase principal del bot de trading"""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.trade_history = []
        self.wins = 0
        self.losses = 0
        self.daily_trades = 0
        self.last_trade_date = None
        self.is_running = False
        self.models_cache = {}
        
        self.initialize_binance()
        
    def initialize_binance(self):
        """Inicializar cliente de Binance"""
        try:
            api_key = self.config.get('binance', 'api_key')
            api_secret = self.config.get('binance', 'api_secret')
            
            if not api_key or not api_secret:
                logger.warning("⚠️ Credenciales de Binance no configuradas")
                return
            
            self.client = Client(api_key, api_secret)
            
            if self.config.get('binance', 'testnet'):
                self.client.API_URL = 'https://testnet.binance.vision/api'
                logger.info("🧪 Modo testnet activado")
            
            # Sincronizar tiempo
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            self.client.timestamp_offset = server_time['serverTime'] - local_time
            
            # Verificar conexión
            account = self.client.get_account()
            logger.info("✅ Conexión a Binance establecida")
            
        except Exception as e:
            logger.error(f"❌ Error al conectar con Binance: {e}")
            self.client = None
    
    def send_telegram_message(self, message: str):
        """Enviar mensaje a Telegram con reintentos"""
        token = self.config.get('telegram', 'token')
        chat_id = self.config.get('telegram', 'chat_id')
        
        if not token or not chat_id:
            logger.warning("⚠️ Telegram no configurado")
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {
                    "chat_id": chat_id, 
                    "text": message,
                    "parse_mode": "Markdown"
                }
                response = requests.post(url, data=payload, timeout=10)
                response.raise_for_status()
                logger.info("✅ Mensaje enviado a Telegram")
                return
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt + 1} fallido: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.error("❌ Error al enviar mensaje a Telegram")
    
    def get_klines(self, symbol: str, interval: str, limit: int = None) -> Optional[pd.DataFrame]:
        """Obtener datos de velas con manejo de errores mejorado"""
        if not self.client:
            return None
        
        if limit is None:
            limit = self.config.get('trading', 'limit')
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                klines = self.client.get_klines(
                    symbol=symbol, 
                    interval=interval, 
                    limit=limit
                )
                
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convertir a tipos numéricos
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Convertir timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                logger.info(f"✅ Datos obtenidos para {symbol} ({interval}): {len(df)} velas")
                return df
                
            except Exception as e:
                logger.warning(f"⚠️ Intento {attempt + 1} fallido para {symbol}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.error(f"❌ Error al obtener datos para {symbol}")
        return None
    
    def apply_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplicar indicadores técnicos mejorados"""
        try:
            df_copy = df.copy()
            
            # EMAs
            df_copy.ta.ema(length=9, append=True)
            df_copy.ta.ema(length=21, append=True)
            df_copy.ta.ema(length=50, append=True)
            df_copy.ta.ema(length=200, append=True)
            
            # Osciladores
            df_copy.ta.rsi(length=14, append=True)
            df_copy.ta.stochrsi(length=14, append=True)
            df_copy.ta.cci(length=20, append=True)
            
            # MACD
            df_copy.ta.macd(append=True)
            
            # Bandas de Bollinger
            df_copy.ta.bbands(length=20, std=2, append=True)
            
            # ADX y direccionalidad
            df_copy.ta.adx(length=14, append=True)
            
            # Volumen
            df_copy.ta.obv(append=True)
            df_copy.ta.ad(append=True)
            
            # Patrones de velas
            df_copy.ta.cdl_doji(append=True)
            df_copy.ta.cdl_hammer(append=True)
            df_copy.ta.cdl_engulfing(append=True)
            
            # Renombrar columnas para consistencia
            column_mapping = {
                'EMA_9': 'ema9',
                'EMA_21': 'ema21', 
                'EMA_50': 'ema50',
                'EMA_200': 'ema200',
                'RSI_14': 'rsi',
                'STOCHRSIk_14_14_3_3': 'stoch_rsi_k',
                'STOCHRSId_14_14_3_3': 'stoch_rsi_d',
                'CCI_20_0.015': 'cci',
                'MACD_12_26_9': 'macd',
                'MACDh_12_26_9': 'macd_histogram',
                'MACDs_12_26_9': 'macd_signal',
                'BBU_20_2.0': 'bb_upper',
                'BBM_20_2.0': 'bb_middle',
                'BBL_20_2.0': 'bb_lower',
                'ADX_14': 'adx',
                'DMP_14': 'dmp',
                'DMN_14': 'dmn',
                'OBV': 'obv',
                'AD': 'ad'
            }
            
            df_copy.rename(columns=column_mapping, inplace=True)
            
            # Calcular características adicionales
            df_copy['price_change'] = df_copy['close'].pct_change()
            df_copy['volatility'] = df_copy['price_change'].rolling(window=20).std()
            df_copy['volume_sma'] = df_copy['volume'].rolling(window=20).mean()
            df_copy['volume_ratio'] = df_copy['volume'] / df_copy['volume_sma']
            
            logger.info("✅ Indicadores técnicos aplicados")
            return df_copy
            
        except Exception as e:
            logger.error(f"❌ Error al aplicar indicadores: {e}")
            return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preparar características para el modelo ML"""
        feature_columns = [
            'ema9', 'ema21', 'ema50', 'ema200',
            'rsi', 'stoch_rsi_k', 'stoch_rsi_d', 'cci',
            'macd', 'macd_histogram', 'macd_signal',
            'adx', 'dmp', 'dmn',
            'price_change', 'volatility', 'volume_ratio'
        ]
        
        # Filtrar solo las columnas que existen
        available_features = [col for col in feature_columns if col in df.columns]
        
        if len(available_features) < 5:
            logger.warning("⚠️ Pocas características disponibles para ML")
            return None, None
        
        # Preparar datos
        df_clean = df[available_features].dropna()
        
        if len(df_clean) < 50:
            logger.warning("⚠️ Datos insuficientes para entrenamiento")
            return None, None
        
        X = df_clean.values
        
        # Crear etiquetas basadas en movimientos futuros
        future_returns = df['close'].shift(-5) / df['close'] - 1
        y = np.where(future_returns > 0.01, 1, np.where(future_returns < -0.01, 0, 2))
        
        # Alinear X e y
        min_len = min(len(X), len(y))
        X = X[:min_len]
        y = y[:min_len]
        
        # Filtrar etiquetas neutras para clasificación binaria
        mask = y != 2
        X = X[mask]
        y = y[mask]
        
        return X, y
    
    def train_model(self, symbol: str, df: pd.DataFrame) -> Optional[object]:
        """Entrenar modelo ML con validación"""
        try:
            X, y = self.prepare_features(df)
            
            if X is None or len(X) < 30:
                logger.warning(f"⚠️ Datos insuficientes para entrenar modelo de {symbol}")
                return None
            
            # División de datos
            test_size = self.config.get('ml', 'test_size')
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Seleccionar modelo
            model_type = self.config.get('ml', 'model_type')
            n_estimators = self.config.get('ml', 'n_estimators')
            
            if model_type == "GradientBoosting":
                model = GradientBoostingClassifier(n_estimators=n_estimators, random_state=42)
            else:
                model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
            
            # Entrenar
            model.fit(X_train, y_train)
            
            # Validar
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            min_accuracy = self.config.get('ml', 'min_accuracy')
            if accuracy < min_accuracy:
                logger.warning(f"⚠️ Precisión del modelo muy baja para {symbol}: {accuracy:.3f}")
                return None
            
            logger.info(f"✅ Modelo entrenado para {symbol} - Precisión: {accuracy:.3f}")
            
            # Cachear modelo
            self.models_cache[symbol] = {
                'model': model,
                'accuracy': accuracy,
                'timestamp': datetime.now()
            }
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error al entrenar modelo para {symbol}: {e}")
            return None
    
    def predict_signal(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Predecir señal de trading con confianza"""
        try:
            # Verificar si hay modelo cacheado válido
            if symbol in self.models_cache:
                cache_entry = self.models_cache[symbol]
                cache_age = datetime.now() - cache_entry['timestamp']
                if cache_age < timedelta(hours=1):  # Usar modelo por 1 hora
                    model = cache_entry['model']
                    accuracy = cache_entry['accuracy']
                else:
                    model = self.train_model(symbol, df)
                    accuracy = self.models_cache.get(symbol, {}).get('accuracy', 0)
            else:
                model = self.train_model(symbol, df)
                accuracy = self.models_cache.get(symbol, {}).get('accuracy', 0)
            
            if model is None:
                return {'signal': 'HOLD', 'confidence': 0, 'accuracy': 0}
            
            # Preparar características para predicción
            X, _ = self.prepare_features(df)
            if X is None:
                return {'signal': 'HOLD', 'confidence': 0, 'accuracy': accuracy}
            
            # Predecir
            X_latest = X[-1:] 
            prediction = model.predict(X_latest)[0]
            probabilities = model.predict_proba(X_latest)[0]
            confidence = max(probabilities)
            
            signal = 'BUY' if prediction == 1 else 'SELL'
            
            # Filtros adicionales
            latest_data = df.iloc[-1]
            
            # Filtro de tendencia
            if 'ema21' in df.columns and 'ema50' in df.columns:
                trend_bullish = latest_data['ema21'] > latest_data['ema50']
                if signal == 'BUY' and not trend_bullish:
                    confidence *= 0.7
                elif signal == 'SELL' and trend_bullish:
                    confidence *= 0.7
            
            # Filtro RSI
            if 'rsi' in df.columns:
                rsi = latest_data['rsi']
                if signal == 'BUY' and rsi > 70:
                    confidence *= 0.5
                elif signal == 'SELL' and rsi < 30:
                    confidence *= 0.5
            
            # Umbral mínimo de confianza
            if confidence < 0.6:
                signal = 'HOLD'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'accuracy': accuracy
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción para {symbol}: {e}")
            return {'signal': 'HOLD', 'confidence': 0, 'accuracy': 0}
    
    def get_balance(self) -> float:
        """Obtener balance de USDT"""
        try:
            if not self.client:
                return 0
            balance = self.client.get_asset_balance(asset='USDT')
            return float(balance['free'])
        except Exception as e:
            logger.error(f"❌ Error al obtener balance: {e}")
            return 0
    
    def check_daily_limits(self) -> bool:
        """Verificar límites diarios de trading"""
        today = datetime.now().date()
        
        if self.last_trade_date != today:
            self.daily_trades = 0
            self.last_trade_date = today
        
        max_trades = self.config.get('trading', 'max_trades_per_day')
        return self.daily_trades < max_trades
    
    def place_order(self, symbol: str, signal: str, confidence: float) -> bool:
        """Colocar orden con gestión de riesgo mejorada"""
        try:
            if not self.client or signal == 'HOLD':
                return False
            
            if not self.check_daily_limits():
                logger.warning("⚠️ Límite diario de trades alcanzado")
                return False
            
            # Verificar balance mínimo
            balance = self.get_balance()
            min_balance = self.config.get('trading', 'min_balance')
            if balance < min_balance:
                logger.warning(f"⚠️ Balance insuficiente: {balance} < {min_balance}")
                return False
            
            # Obtener información del símbolo
            exchange_info = self.client.get_exchange_info()
            symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
            if not symbol_info:
                logger.error(f"❌ Símbolo {symbol} no encontrado")
                return False
            
            # Obtener precio actual
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Calcular cantidad basada en confianza
            base_risk = self.config.get('trading', 'risk_percentage')
            adjusted_risk = base_risk * confidence  # Ajustar riesgo por confianza
            amount_to_use = balance * (adjusted_risk / 100)
            
            # Obtener filtros del símbolo
            lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            if not lot_size_filter:
                logger.error(f"❌ No se pudo obtener LOT_SIZE para {symbol}")
                return False
            
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            
            # Calcular cantidad
            quantity = amount_to_use / price
            quantity = math.floor(quantity / step_size) * step_size
            
            if quantity < min_qty:
                logger.warning(f"⚠️ Cantidad muy pequeña para {symbol}: {quantity} < {min_qty}")
                return False
            
            # Formatear cantidad
            precision = int(round(-math.log(step_size, 10), 0))
            quantity_str = f"{quantity:.{precision}f}"
            
            # Calcular TP y SL
            tp_pct = self.config.get('trading', 'tp_percentage')
            sl_pct = self.config.get('trading', 'sl_percentage')
            
            if signal == 'BUY':
                tp_price = price * (1 + tp_pct / 100)
                sl_price = price * (1 - sl_pct / 100)
            else:
                tp_price = price * (1 - tp_pct / 100)
                sl_price = price * (1 + sl_pct / 100)
            
            # Ejecutar orden
            if signal == 'BUY':
                order = self.client.order_market_buy(symbol=symbol, quantity=quantity_str)
            else:
                order = self.client.order_market_sell(symbol=symbol, quantity=quantity_str)
            
            # Registrar trade
            trade_data = {
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'symbol': symbol,
                'signal': signal,
                'entry': price,
                'quantity': quantity,
                'tp': tp_price,
                'sl': sl_price,
                'confidence': confidence,
                'order_id': order['orderId']
            }
            
            self.trade_history.append(trade_data)
            self.daily_trades += 1
            
            # Mensaje de confirmación
            mensaje = (f"✅ *Orden {signal} ejecutada*\n"
                      f"📊 Par: `{symbol}`\n"
                      f"💰 Precio: `${price:.4f}`\n"
                      f"📈 TP: `${tp_price:.4f}` ({tp_pct}%)\n"
                      f"📉 SL: `${sl_price:.4f}` ({sl_pct}%)\n"
                      f"🎯 Confianza: `{confidence:.1%}`\n"
                      f"💼 Cantidad: `{quantity:.6f}`")
            
            logger.info(mensaje.replace('*', '').replace('`', ''))
            self.send_telegram_message(mensaje)
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Error al colocar orden en {symbol}: {str(e)}"
            logger.error(error_msg)
            self.send_telegram_message(error_msg)
            return False
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """Analizar un símbolo específico"""
        try:
            # Obtener datos de múltiples timeframes
            timeframes = self.config.get('trading', 'timeframes')
            signals = {}
            
            for tf in timeframes:
                df = self.get_klines(symbol, tf)
                if df is None:
                    continue
                
                df = self.apply_indicators(df)
                signal_data = self.predict_signal(symbol, df)
                signals[tf] = signal_data
            
            if not signals:
                return {'symbol': symbol, 'action': 'HOLD', 'reason': 'No data available'}
            
            # Combinar señales de diferentes timeframes
            buy_votes = sum(1 for s in signals.values() if s['signal'] == 'BUY')
            sell_votes = sum(1 for s in signals.values() if s['signal'] == 'SELL')
            
            avg_confidence = np.mean([s['confidence'] for s in signals.values()])
            avg_accuracy = np.mean([s['accuracy'] for s in signals.values() if s['accuracy'] > 0])
            
            # Decidir acción final
            if buy_votes > sell_votes and avg_confidence > 0.6:
                action = 'BUY'
            elif sell_votes > buy_votes and avg_confidence > 0.6:
                action = 'SELL'
            else:
                action = 'HOLD'
            
            result = {
                'symbol': symbol,
                'action': action,
                'confidence': avg_confidence,
                'accuracy': avg_accuracy,
                'signals': signals,
                'votes': {'buy': buy_votes, 'sell': sell_votes}
            }
            
            # Ejecutar orden si es necesario
            if action in ['BUY', 'SELL']:
                success = self.place_order(symbol, action, avg_confidence)
                result['order_placed'] = success
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error al analizar {symbol}: {e}")
            return {'symbol': symbol, 'action': 'HOLD', 'reason': str(e)}
    
    def run_analysis(self) -> List[Dict]:
        """Ejecutar análisis completo de todos los símbolos"""
        symbols = self.config.get('trading', 'symbols')
        results = []
        
        logger.info(f"🚀 Iniciando análisis de {len(symbols)} símbolos")
        
        for symbol in symbols:
            if not self.is_running:
                break
            
            result = self.analyze_symbol(symbol)
            results.append(result)
            
            # Pausa entre análisis
            time.sleep(1)
        
        # Resumen
        actions = [r['action'] for r in results]
        summary = {
            'total': len(results),
            'buy': actions.count('BUY'),
            'sell': actions.count('SELL'),
            'hold': actions.count('HOLD')
        }
        
        logger.info(f"📊 Resumen: {summary}")
        
        return results

class TradingBotGUI:
    """Interfaz gráfica mejorada para el trading bot"""
    
    def __init__(self):
        self.bot = TradingBot()
        self.root = tk.Tk()
        self.setup_ui()
        self.running = False
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        self.root.title("🚀 Advanced Trading Bot v2.0")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a1a")
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background="#1a1a1a", foreground="#00ff00")
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'), background="#1a1a1a", foreground="#ffffff")
        
        # Título
        title_frame = tk.Frame(self.root, bg="#1a1a1a")
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="🚀 Advanced Trading Bot v2.0", style='Title.TLabel')
        title_label.pack()
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Pestaña de Trading
        self.trading_frame = ttk.Frame(notebook)
        notebook.add(self.trading_frame, text="🎯 Trading")
        self.setup_trading_tab()
        
        # Pestaña de Configuración
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="⚙️ Config")
        self.setup_config_tab()
        
        # Pestaña de Estadísticas
        self.stats_frame = ttk.Frame(notebook)
        notebook.add(self.stats_frame, text="📊 Stats")
        self.setup_stats_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Bot listo")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_trading_tab(self):
        """Configurar pestaña de trading"""
        # Frame de control
        control_frame = ttk.LabelFrame(self.trading_frame, text="Control de Trading")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones principales
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = tk.Button(btn_frame, text="▶️ Iniciar", command=self.start_trading,
                                  bg="#00aa00", fg="white", font=('Arial', 12, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Detener", command=self.stop_trading,
                                 bg="#aa0000", fg="white", font=('Arial', 12, 'bold'), state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = tk.Button(btn_frame, text="🔍 Análisis Manual", command=self.manual_analysis,
                                    bg="#0066cc", fg="white", font=('Arial', 12, 'bold'))
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # Información de cuenta
        info_frame = ttk.LabelFrame(self.trading_frame, text="Información de Cuenta")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.balance_var = tk.StringVar()
        self.trades_var = tk.StringVar()
        self.winrate_var = tk.StringVar()
        
        ttk.Label(info_frame, text="💰 Balance USDT:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(info_frame, textvariable=self.balance_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="📈 Trades hoy:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Label(info_frame, textvariable=self.trades_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(info_frame, text="🎯 Win Rate:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Label(info_frame, textvariable=self.winrate_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Log de resultados
        log_frame = ttk.LabelFrame(self.trading_frame, text="Log de Actividad")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, bg="#000000", fg="#00ff00",
                                                 font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.update_info()
    
    def setup_config_tab(self):
        """Configurar pestaña de configuración"""
        # Trading Config
        trading_frame = ttk.LabelFrame(self.config_frame, text="Configuración de Trading")
        trading_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Risk percentage
        ttk.Label(trading_frame, text="Riesgo por trade (%):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.risk_var = tk.StringVar(value=str(self.bot.config.get('trading', 'risk_percentage')))
        risk_entry = ttk.Entry(trading_frame, textvariable=self.risk_var, width=10)
        risk_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # TP percentage
        ttk.Label(trading_frame, text="Take Profit (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.tp_var = tk.StringVar(value=str(self.bot.config.get('trading', 'tp_percentage')))
        tp_entry = ttk.Entry(trading_frame, textvariable=self.tp_var, width=10)
        tp_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # SL percentage
        ttk.Label(trading_frame, text="Stop Loss (%):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.sl_var = tk.StringVar(value=str(self.bot.config.get('trading', 'sl_percentage')))
        sl_entry = ttk.Entry(trading_frame, textvariable=self.sl_var, width=10)
        sl_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # Max trades per day
        ttk.Label(trading_frame, text="Max trades/día:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_trades_var = tk.StringVar(value=str(self.bot.config.get('trading', 'max_trades_per_day')))
        max_trades_entry = ttk.Entry(trading_frame, textvariable=self.max_trades_var, width=10)
        max_trades_entry.grid(row=3, column=1, padx=5, pady=2)
        
        # Símbolos
        symbols_frame = ttk.LabelFrame(self.config_frame, text="Símbolos de Trading")
        symbols_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.symbols_text = tk.Text(symbols_frame, height=5, width=50)
        symbols_list = self.bot.config.get('trading', 'symbols')
        self.symbols_text.insert('1.0', ', '.join(symbols_list))
        self.symbols_text.pack(padx=5, pady=5)
        
        # Botón guardar
        save_btn = tk.Button(self.config_frame, text="💾 Guardar Configuración", 
                           command=self.save_config, bg="#0066cc", fg="white")
        save_btn.pack(pady=10)
    
    def setup_stats_tab(self):
        """Configurar pestaña de estadísticas"""
        # Resumen de trades
        summary_frame = ttk.LabelFrame(self.stats_frame, text="Resumen de Trades")
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.total_trades_var = tk.StringVar()
        self.wins_var = tk.StringVar()
        self.losses_var = tk.StringVar()
        self.win_rate_var = tk.StringVar()
        
        ttk.Label(summary_frame, text="Total Trades:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(summary_frame, textvariable=self.total_trades_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(summary_frame, text="Ganados:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Label(summary_frame, textvariable=self.wins_var, foreground="green").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(summary_frame, text="Perdidos:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Label(summary_frame, textvariable=self.losses_var, foreground="red").grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(summary_frame, text="Win Rate:").grid(row=3, column=0, sticky=tk.W, padx=5)
        ttk.Label(summary_frame, textvariable=self.win_rate_var).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Historial de trades
        history_frame = ttk.LabelFrame(self.stats_frame, text="Historial de Trades")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview para el historial
        columns = ('Fecha', 'Símbolo', 'Señal', 'Precio', 'TP', 'SL', 'Confianza')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_stats()
    
    def update_info(self):
        """Actualizar información de la cuenta"""
        try:
            balance = self.bot.get_balance()
            self.balance_var.set(f"${balance:.2f}")
            self.trades_var.set(str(self.bot.daily_trades))
            
            total = self.bot.wins + self.bot.losses
            if total > 0:
                winrate = (self.bot.wins / total) * 100
                self.winrate_var.set(f"{winrate:.1f}%")
            else:
                self.winrate_var.set("N/A")
                
        except Exception as e:
            logger.error(f"Error updating info: {e}")
        
        # Programar próxima actualización
        self.root.after(5000, self.update_info)
    
    def update_stats(self):
        """Actualizar estadísticas"""
        try:
            total = len(self.bot.trade_history)
            wins = self.bot.wins
            losses = self.bot.losses
            
            self.total_trades_var.set(str(total))
            self.wins_var.set(str(wins))
            self.losses_var.set(str(losses))
            
            if total > 0:
                winrate = (wins / total) * 100
                self.win_rate_var.set(f"{winrate:.1f}%")
            else:
                self.win_rate_var.set("N/A")
            
            # Actualizar historial
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            for trade in self.bot.trade_history[-20:]:  # Últimos 20 trades
                values = (
                    trade['fecha'],
                    trade['symbol'],
                    trade['signal'],
                    f"${trade['entry']:.4f}",
                    f"${trade['tp']:.4f}",
                    f"${trade['sl']:.4f}",
                    f"{trade['confidence']:.1%}"
                )
                self.history_tree.insert('', 0, values=values)
                
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    def log_message(self, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limitar líneas del log
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")
    
    def start_trading(self):
        """Iniciar trading automático"""
        if not self.bot.client:
            messagebox.showerror("Error", "No hay conexión con Binance")
            return
        
        self.running = True
        self.bot.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🟡 Bot ejecutándose...")
        
        self.log_message("🚀 Bot de trading iniciado")
        
        # Iniciar thread de trading
        trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
        trading_thread.start()
    
    def stop_trading(self):
        """Detener trading automático"""
        self.running = False
        self.bot.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("🔴 Bot detenido")
        
        self.log_message("⏹️ Bot de trading detenido")
    
    def trading_loop(self):
        """Loop principal de trading"""
        while self.running:
            try:
                self.log_message("🔍 Iniciando análisis de mercado...")
                results = self.bot.run_analysis()
                
                for result in results:
                    if not self.running:
                        break
                    
                    symbol = result['symbol']
                    action = result['action']
                    confidence = result.get('confidence', 0)
                    
                    if action != 'HOLD':
                        msg = f"📊 {symbol}: {action} (Confianza: {confidence:.1%})"
                        if result.get('order_placed'):
                            msg += " ✅ Orden ejecutada"
                        else:
                            msg += " ❌ Orden no ejecutada"
                        self.log_message(msg)
                    else:
                        self.log_message(f"⏸️ {symbol}: HOLD")
                
                # Actualizar estadísticas
                self.root.after(0, self.update_stats)
                
                # Esperar antes del próximo análisis (15 minutos)
                for _ in range(900):  # 900 segundos = 15 minutos
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_message(f"❌ Error en trading loop: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def manual_analysis(self):
        """Ejecutar análisis manual"""
        if not self.bot.client:
            messagebox.showerror("Error", "No hay conexión con Binance")
            return
        
        self.log_message("🔍 Ejecutando análisis manual...")
        
        # Ejecutar en thread separado para no bloquear UI
        analysis_thread = threading.Thread(target=self._run_manual_analysis, daemon=True)
        analysis_thread.start()
    
    def _run_manual_analysis(self):
        """Ejecutar análisis manual en thread separado"""
        try:
            results = self.bot.run_analysis()
            
            for result in results:
                symbol = result['symbol']
                action = result['action']
                confidence = result.get('confidence', 0)
                
                msg = f"📊 {symbol}: {action}"
                if confidence > 0:
                    msg += f" (Confianza: {confidence:.1%})"
                
                self.root.after(0, lambda m=msg: self.log_message(m))
            
            self.root.after(0, lambda: self.log_message("✅ Análisis manual completado"))
            self.root.after(0, self.update_stats)
            
        except Exception as e:
            error_msg = f"❌ Error en análisis manual: {e}"
            self.root.after(0, lambda: self.log_message(error_msg))
    
    def save_config(self):
        """Guardar configuración"""
        try:
            # Actualizar configuración
            self.bot.config.config['trading']['risk_percentage'] = float(self.risk_var.get())
            self.bot.config.config['trading']['tp_percentage'] = float(self.tp_var.get())
            self.bot.config.config['trading']['sl_percentage'] = float(self.sl_var.get())
            self.bot.config.config['trading']['max_trades_per_day'] = int(self.max_trades_var.get())
            
            # Actualizar símbolos
            symbols_text = self.symbols_text.get("1.0", tk.END).strip()
            symbols = [s.strip() for s in symbols_text.split(',') if s.strip()]
            self.bot.config.config['trading']['symbols'] = symbols
            
            # Guardar
            self.bot.config.save_config()
            
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            self.log_message("💾 Configuración guardada")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {e}")
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("👋 Aplicación cerrada por el usuario")

def main():
    """Función principal"""
    try:
        app = TradingBotGUI()
        app.run()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")

if __name__ == "__main__":
    main()
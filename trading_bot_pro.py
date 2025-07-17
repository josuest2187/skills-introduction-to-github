#!/usr/bin/env python3
"""
🤖 TRADING BOT PRO - Versión de Producción
Bot de trading profesional con ML, gestión de riesgo y seguridad
"""

import os
import sys
import logging
import time
import threading
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import requests
from binance.client import Client
from binance.enums import *
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Importar módulos propios
from config import ConfigManager, TradingConfig
from database import TradingDatabase
from risk_manager import RiskManager
from ml_strategy import MLStrategy

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBotPro:
    """Bot de trading profesional con todas las características de producción"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.db = TradingDatabase()
        self.risk_manager = RiskManager(self.config, self.db)
        self.ml_strategy = MLStrategy(self.config)
        
        # Cliente de Binance
        self.client = None
        self.running = False
        self.last_balance_update = datetime.now()
        
        # Inicializar componentes
        self._initialize_components()
        
    def _initialize_components(self):
        """Inicializa todos los componentes del bot"""
        
        try:
            # Validar configuración
            self.config_manager.validate_config()
            
            # Inicializar cliente de Binance
            if not self.config.demo_mode:
                self.client = Client(
                    self.config.binance_api_key,
                    self.config.binance_api_secret
                )
                # Verificar conexión
                account_info = self.client.get_account()
                logger.info("✅ Conexión con Binance establecida")
            else:
                logger.info("🔄 Modo DEMO activado - no se ejecutarán órdenes reales")
            
            # Cargar modelos ML
            self.ml_strategy.load_models()
            
            # Configurar manejador de señales
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("✅ Bot inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando bot: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema para cierre limpio"""
        logger.info(f"🛑 Señal recibida: {signum}")
        self.stop_bot()
    
    def start_bot(self):
        """Inicia el bot de trading"""
        
        if self.running:
            logger.warning("⚠️ El bot ya está ejecutándose")
            return
        
        self.running = True
        logger.info("🚀 Iniciando Trading Bot Pro...")
        
        # Enviar notificación de inicio
        self._send_telegram(f"🚀 Trading Bot Pro iniciado\n"
                           f"Modo: {'DEMO' if self.config.demo_mode else 'REAL'}\n"
                           f"Símbolos: {', '.join(self.config.symbols)}\n"
                           f"Timeframes: {', '.join(self.config.timeframes)}")
        
        # Actualizar balance inicial
        self._update_account_balance()
        
        # Iniciar hilos de trabajo
        self._start_worker_threads()
        
        logger.info("✅ Bot iniciado exitosamente")
    
    def stop_bot(self):
        """Detiene el bot de trading"""
        
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo Trading Bot Pro...")
        self.running = False
        
        # Cerrar todas las posiciones abiertas si es necesario
        if self.risk_manager.emergency_stop():
            self._close_all_positions()
        
        # Enviar notificación de cierre
        self._send_telegram("🛑 Trading Bot Pro detenido")
        
        logger.info("✅ Bot detenido correctamente")
    
    def _start_worker_threads(self):
        """Inicia los hilos de trabajo del bot"""
        
        # Hilo principal de trading
        trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        trading_thread.start()
        
        # Hilo de monitoreo de posiciones
        monitoring_thread = threading.Thread(target=self._position_monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        # Hilo de actualización de balance
        balance_thread = threading.Thread(target=self._balance_update_loop, daemon=True)
        balance_thread.start()
    
    def _trading_loop(self):
        """Bucle principal de trading"""
        
        while self.running:
            try:
                # Verificar parada de emergencia
                if self.risk_manager.emergency_stop():
                    logger.critical("🚨 PARADA DE EMERGENCIA ACTIVADA")
                    self._close_all_positions()
                    break
                
                # Analizar cada símbolo y timeframe
                for symbol in self.config.symbols:
                    for timeframe in self.config.timeframes:
                        if not self.running:
                            break
                        
                        self._analyze_symbol(symbol, timeframe)
                        time.sleep(1)  # Evitar límites de API
                
                # Registrar estado de riesgo
                self.risk_manager.log_risk_status()
                
                # Esperar antes del siguiente ciclo
                time.sleep(60)  # Análisis cada minuto
                
            except Exception as e:
                logger.error(f"❌ Error en bucle de trading: {e}")
                time.sleep(30)
    
    def _position_monitoring_loop(self):
        """Bucle de monitoreo de posiciones"""
        
        while self.running:
            try:
                open_positions = self.db.get_open_positions()
                
                for position in open_positions:
                    current_price = self._get_current_price(position['symbol'])
                    if current_price is None:
                        continue
                    
                    # Actualizar precio actual
                    self.db.update_position(position['id'], {'current_price': current_price})
                    
                    # Calcular PnL
                    pnl = self._calculate_pnl(position, current_price)
                    self.db.update_position(position['id'], {'pnl': pnl})
                    
                    # Verificar si se debe cerrar
                    should_close, reason = self.risk_manager.should_close_position(position, current_price)
                    
                    if should_close:
                        logger.info(f"🔄 Cerrando posición: {reason}")
                        self._close_position(position, current_price, reason)
                
                time.sleep(10)  # Monitoreo cada 10 segundos
                
            except Exception as e:
                logger.error(f"❌ Error en monitoreo de posiciones: {e}")
                time.sleep(30)
    
    def _balance_update_loop(self):
        """Bucle de actualización de balance"""
        
        while self.running:
            try:
                # Actualizar balance cada 5 minutos
                if datetime.now() - self.last_balance_update > timedelta(minutes=5):
                    self._update_account_balance()
                    self.last_balance_update = datetime.now()
                
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Error actualizando balance: {e}")
                time.sleep(60)
    
    def _analyze_symbol(self, symbol: str, timeframe: str):
        """Analiza un símbolo específico"""
        
        try:
            # Obtener datos históricos
            df = self._get_klines(symbol, timeframe)
            if df is None or len(df) < 100:
                return
            
            # Generar señal ML
            signal_data = self.ml_strategy.predict_signal(symbol, timeframe, df)
            if signal_data is None:
                return
            
            # Guardar señal en base de datos
            self.db.save_signal(signal_data)
            
            # Verificar si podemos abrir posición
            current_price = signal_data['price']
            quantity = self.risk_manager.calculate_position_size(
                symbol, current_price, signal_data['confidence']
            )
            
            can_open, reason = self.risk_manager.can_open_position(
                symbol, signal_data['signal'], quantity, current_price
            )
            
            if can_open:
                self._execute_trade(signal_data, quantity)
            else:
                logger.info(f"⚠️ Posición rechazada: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Error analizando {symbol} [{timeframe}]: {e}")
    
    def _execute_trade(self, signal_data: Dict, quantity: float):
        """Ejecuta una operación de trading"""
        
        try:
            symbol = signal_data['symbol']
            side = signal_data['signal']
            price = signal_data['price']
            confidence = signal_data['confidence']
            
            # Calcular stop loss y take profit
            stop_loss = self.risk_manager.calculate_stop_loss(price, side)
            take_profit = self.risk_manager.calculate_take_profit(price, side)
            
            if self.config.demo_mode:
                # Modo demo - simular orden
                order_result = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': quantity,
                    'price': price,
                    'status': 'FILLED',
                    'orderId': f"demo_{int(time.time())}"
                }
                logger.info(f"🎯 [DEMO] {side} {quantity} {symbol} @ {price}")
            else:
                # Modo real - ejecutar orden
                if side == 'BUY':
                    order_result = self.client.order_market_buy(
                        symbol=symbol,
                        quantity=quantity
                    )
                else:
                    order_result = self.client.order_market_sell(
                        symbol=symbol,
                        quantity=quantity
                    )
                
                logger.info(f"✅ Orden ejecutada: {order_result['orderId']}")
            
            # Guardar posición en base de datos
            position_data = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timeframe': signal_data['timeframe'],
                'strategy': 'ML',
                'confidence': confidence
            }
            
            position_id = self.db.save_position(position_data)
            
            # Guardar orden
            order_data = {
                'binance_order_id': order_result.get('orderId'),
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity,
                'price': price,
                'status': order_result.get('status', 'FILLED'),
                'position_id': position_id
            }
            
            self.db.save_order(order_data)
            
            # Enviar notificación
            message = f"🎯 Nueva posición:\n"
            message += f"📊 {symbol} - {side}\n"
            message += f"💰 Cantidad: {quantity}\n"
            message += f"💵 Precio: {price}\n"
            message += f"🔴 SL: {stop_loss}\n"
            message += f"🟢 TP: {take_profit}\n"
            message += f"🎯 Confianza: {confidence:.2%}"
            
            self._send_telegram(message)
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando trade: {e}")
            self._send_telegram(f"❌ Error ejecutando trade: {e}")
    
    def _close_position(self, position: Dict, current_price: float, reason: str):
        """Cierra una posición"""
        
        try:
            symbol = position['symbol']
            side = 'SELL' if position['side'] == 'BUY' else 'BUY'
            quantity = position['quantity']
            
            if self.config.demo_mode:
                # Modo demo
                logger.info(f"🔄 [DEMO] Cerrando posición {symbol} - {reason}")
            else:
                # Modo real
                if side == 'BUY':
                    order_result = self.client.order_market_buy(
                        symbol=symbol,
                        quantity=quantity
                    )
                else:
                    order_result = self.client.order_market_sell(
                        symbol=symbol,
                        quantity=quantity
                    )
                
                logger.info(f"✅ Posición cerrada: {order_result['orderId']}")
            
            # Calcular PnL final
            pnl = self._calculate_pnl(position, current_price)
            
            # Actualizar posición
            self.db.update_position(position['id'], {
                'status': 'CLOSED',
                'current_price': current_price,
                'pnl': pnl,
                'exit_time': datetime.now()
            })
            
            # Enviar notificación
            pnl_emoji = "🟢" if pnl > 0 else "🔴"
            message = f"{pnl_emoji} Posición cerrada:\n"
            message += f"📊 {symbol} - {position['side']}\n"
            message += f"💰 PnL: {pnl:.4f}\n"
            message += f"📝 Razón: {reason}"
            
            self._send_telegram(message)
            
        except Exception as e:
            logger.error(f"❌ Error cerrando posición: {e}")
    
    def _close_all_positions(self):
        """Cierra todas las posiciones abiertas"""
        
        open_positions = self.db.get_open_positions()
        
        for position in open_positions:
            current_price = self._get_current_price(position['symbol'])
            if current_price:
                self._close_position(position, current_price, "Cierre de emergencia")
    
    def _get_klines(self, symbol: str, interval: str, limit: int = None) -> Optional[pd.DataFrame]:
        """Obtiene datos de velas de Binance"""
        
        try:
            limit = limit or self.config.lookback_periods
            
            if self.config.demo_mode:
                # En modo demo, usar datos simulados o API pública
                from binance.client import Client
                demo_client = Client()
                data = demo_client.get_klines(symbol=symbol, interval=interval, limit=limit)
            else:
                data = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'num_trades',
                'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            
            # Convertir tipos de datos
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de {symbol}: {e}")
            return None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Obtiene el precio actual de un símbolo"""
        
        try:
            if self.config.demo_mode:
                # Usar API pública para precio
                from binance.client import Client
                demo_client = Client()
                ticker = demo_client.get_symbol_ticker(symbol=symbol)
            else:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
            
            return float(ticker['price'])
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo precio de {symbol}: {e}")
            return None
    
    def _calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Calcula el PnL de una posición"""
        
        entry_price = position['entry_price']
        quantity = position['quantity']
        side = position['side']
        
        if side == 'BUY':
            pnl = (current_price - entry_price) * quantity
        else:
            pnl = (entry_price - current_price) * quantity
        
        return pnl
    
    def _update_account_balance(self):
        """Actualiza el balance de la cuenta"""
        
        try:
            if self.config.demo_mode:
                # Balance simulado
                balance_data = {
                    'total_balance': 1000.0,
                    'available_balance': 950.0,
                    'locked_balance': 50.0,
                    'pnl_today': self.db.get_daily_pnl()
                }
            else:
                account = self.client.get_account()
                usdt_balance = next(
                    (b for b in account['balances'] if b['asset'] == 'USDT'),
                    {'free': '0', 'locked': '0'}
                )
                
                balance_data = {
                    'total_balance': float(usdt_balance['free']) + float(usdt_balance['locked']),
                    'available_balance': float(usdt_balance['free']),
                    'locked_balance': float(usdt_balance['locked']),
                    'pnl_today': self.db.get_daily_pnl()
                }
            
            self.db.save_account_balance(balance_data)
            self.risk_manager.update_daily_balance(balance_data['total_balance'])
            
        except Exception as e:
            logger.error(f"❌ Error actualizando balance: {e}")
    
    def _send_telegram(self, message: str):
        """Envía mensaje a Telegram"""
        
        try:
            if not self.config.telegram_token or not self.config.telegram_chat_id:
                return
            
            url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.config.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code != 200:
                logger.warning(f"⚠️ Error enviando Telegram: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando Telegram: {e}")
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del bot"""
        
        return {
            'running': self.running,
            'demo_mode': self.config.demo_mode,
            'symbols': self.config.symbols,
            'timeframes': self.config.timeframes,
            'open_positions': len(self.db.get_open_positions()),
            'daily_pnl': self.db.get_daily_pnl(),
            'risk_metrics': self.risk_manager.get_risk_metrics()
        }

class TradingBotGUI:
    """Interfaz gráfica para el bot de trading"""
    
    def __init__(self):
        self.bot = TradingBotPro()
        self.setup_gui()
    
    def setup_gui(self):
        """Configura la interfaz gráfica"""
        
        self.root = tk.Tk()
        self.root.title("🤖 Trading Bot Pro")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#2b2b2b', foreground='white')
        style.configure('TButton', background='#4a4a4a', foreground='white')
        style.configure('TFrame', background='#2b2b2b')
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crea los widgets de la interfaz"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="🤖 Trading Bot Pro", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Estado del bot
        self.status_label = ttk.Label(main_frame, text="Estado: Detenido", 
                                     font=('Arial', 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Botones de control
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶️ Iniciar Bot", 
                                      command=self.start_bot)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Detener Bot", 
                                     command=self.stop_bot, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Información de configuración
        config_frame = ttk.LabelFrame(main_frame, text="Configuración", padding="10")
        config_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(config_frame, text=f"Modo: {'DEMO' if self.bot.config.demo_mode else 'REAL'}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(config_frame, text=f"Símbolos: {', '.join(self.bot.config.symbols)}").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(config_frame, text=f"Timeframes: {', '.join(self.bot.config.timeframes)}").grid(row=2, column=0, sticky=tk.W)
        
        # Log de salida
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=70, height=15, 
                                                 bg='black', fg='lime', font=('Courier', 10))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar redimensionamiento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Actualizar estado periódicamente
        self.update_status()
    
    def start_bot(self):
        """Inicia el bot"""
        try:
            self.bot.start_bot()
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text="Estado: ✅ Ejecutándose")
            self.log_message("✅ Bot iniciado correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando bot: {e}")
    
    def stop_bot(self):
        """Detiene el bot"""
        self.bot.stop_bot()
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Estado: ⏹️ Detenido")
        self.log_message("⏹️ Bot detenido")
    
    def log_message(self, message: str):
        """Añade mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self):
        """Actualiza el estado de la interfaz"""
        try:
            status = self.bot.get_status()
            
            if status['running']:
                self.status_label.config(text=f"Estado: ✅ Ejecutándose - "
                                           f"Posiciones: {status['open_positions']} - "
                                           f"PnL: {status['daily_pnl']:.4f}")
            
        except Exception as e:
            pass
        
        # Programar siguiente actualización
        self.root.after(5000, self.update_status)
    
    def run(self):
        """Ejecuta la interfaz gráfica"""
        self.root.mainloop()

def main():
    """Función principal"""
    
    # Crear directorio de modelos si no existe
    os.makedirs('models', exist_ok=True)
    
    # Verificar si se ejecuta en modo CLI o GUI
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # Modo CLI
        bot = TradingBotPro()
        
        try:
            bot.start_bot()
            
            # Mantener el bot ejecutándose
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrupción del usuario")
            bot.stop_bot()
        
    else:
        # Modo GUI
        app = TradingBotGUI()
        app.run()

if __name__ == "__main__":
    main()
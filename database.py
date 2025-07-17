import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import logging

logger = logging.getLogger(__name__)

class TradingDatabase:
    """Base de datos para almacenar datos de trading"""
    
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de posiciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    status TEXT DEFAULT 'OPEN',
                    pnl REAL DEFAULT 0,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    timeframe TEXT,
                    strategy TEXT,
                    confidence REAL
                )
            """)
            
            # Tabla de órdenes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    binance_order_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL,
                    status TEXT NOT NULL,
                    filled_quantity REAL DEFAULT 0,
                    commission REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    position_id INTEGER,
                    FOREIGN KEY (position_id) REFERENCES positions (id)
                )
            """)
            
            # Tabla de señales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    price REAL NOT NULL,
                    indicators TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabla de rendimiento diario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    starting_balance REAL NOT NULL,
                    ending_balance REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    total_trades INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    losing_trades INTEGER NOT NULL,
                    max_drawdown REAL,
                    volume_traded REAL
                )
            """)
            
            # Tabla de balance de cuenta
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_balance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_balance REAL NOT NULL,
                    available_balance REAL NOT NULL,
                    locked_balance REAL NOT NULL,
                    pnl_today REAL DEFAULT 0
                )
            """)
            
            conn.commit()
            logger.info("✅ Base de datos inicializada correctamente")
    
    def save_position(self, position_data: Dict) -> int:
        """Guarda una nueva posición en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO positions (symbol, side, quantity, entry_price, stop_loss, 
                                     take_profit, timeframe, strategy, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position_data['symbol'],
                position_data['side'],
                position_data['quantity'],
                position_data['entry_price'],
                position_data['stop_loss'],
                position_data['take_profit'],
                position_data['timeframe'],
                position_data['strategy'],
                position_data['confidence']
            ))
            position_id = cursor.lastrowid
            conn.commit()
            return position_id
    
    def update_position(self, position_id: int, updates: Dict):
        """Actualiza una posición existente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [position_id]
            
            cursor.execute(f"""
                UPDATE positions SET {set_clause} WHERE id = ?
            """, values)
            conn.commit()
    
    def get_open_positions(self) -> List[Dict]:
        """Obtiene todas las posiciones abiertas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM positions WHERE status = 'OPEN'
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_positions_by_symbol(self, symbol: str) -> List[Dict]:
        """Obtiene posiciones por símbolo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN'
            """, (symbol,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def save_order(self, order_data: Dict) -> int:
        """Guarda una orden en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (binance_order_id, symbol, side, type, quantity, 
                                  price, status, filled_quantity, commission, position_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_data.get('binance_order_id'),
                order_data['symbol'],
                order_data['side'],
                order_data['type'],
                order_data['quantity'],
                order_data.get('price', 0),
                order_data['status'],
                order_data.get('filled_quantity', 0),
                order_data.get('commission', 0),
                order_data.get('position_id')
            ))
            order_id = cursor.lastrowid
            conn.commit()
            return order_id
    
    def save_signal(self, signal_data: Dict) -> int:
        """Guarda una señal generada"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals (symbol, timeframe, signal, confidence, price, indicators)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                signal_data['symbol'],
                signal_data['timeframe'],
                signal_data['signal'],
                signal_data['confidence'],
                signal_data['price'],
                json.dumps(signal_data.get('indicators', {}))
            ))
            signal_id = cursor.lastrowid
            conn.commit()
            return signal_id
    
    def get_daily_pnl(self, date: str = None) -> float:
        """Obtiene el PnL del día especificado"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(pnl), 0) FROM positions 
                WHERE DATE(entry_time) = ? AND status = 'CLOSED'
            """, (date,))
            return cursor.fetchone()[0]
    
    def get_account_balance(self) -> Optional[Dict]:
        """Obtiene el último balance de cuenta"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM account_balance 
                ORDER BY timestamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def save_account_balance(self, balance_data: Dict):
        """Guarda el balance de cuenta"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO account_balance (total_balance, available_balance, 
                                           locked_balance, pnl_today)
                VALUES (?, ?, ?, ?)
            """, (
                balance_data['total_balance'],
                balance_data['available_balance'],
                balance_data['locked_balance'],
                balance_data['pnl_today']
            ))
            conn.commit()
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Obtiene estadísticas de rendimiento"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MAX(pnl) as max_win,
                    MIN(pnl) as max_loss
                FROM positions 
                WHERE status = 'CLOSED' AND entry_time >= datetime('now', '-{} days')
            """.format(days))
            
            stats = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            performance = dict(zip(columns, stats))
            
            # Calcular win rate
            if performance['total_trades'] > 0:
                performance['win_rate'] = performance['winning_trades'] / performance['total_trades']
            else:
                performance['win_rate'] = 0
            
            return performance
    
    def cleanup_old_data(self, days: int = 90):
        """Limpia datos antiguos para mantener la base de datos optimizada"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Eliminar señales antiguas
            cursor.execute("""
                DELETE FROM signals 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            
            # Eliminar balances antiguos (mantener solo uno por día)
            cursor.execute("""
                DELETE FROM account_balance 
                WHERE id NOT IN (
                    SELECT MIN(id) FROM account_balance 
                    GROUP BY DATE(timestamp)
                ) AND timestamp < datetime('now', '-{} days')
            """.format(days))
            
            conn.commit()
            logger.info(f"🧹 Datos antiguos limpiados ({days} días)")
    
    def export_to_csv(self, table: str, filename: str = None):
        """Exporta una tabla a CSV"""
        if filename is None:
            filename = f"{table}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            df.to_csv(filename, index=False)
            logger.info(f"📊 Tabla {table} exportada a {filename}")
    
    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        return sqlite3.connect(self.db_path)
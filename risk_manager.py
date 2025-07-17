import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from database import TradingDatabase
from config import TradingConfig

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Métricas de riesgo actuales"""
    daily_pnl: float
    open_positions: int
    total_exposure: float
    max_drawdown: float
    win_rate: float
    sharpe_ratio: float
    var_95: float  # Value at Risk 95%

class RiskManager:
    """Gestor de riesgo avanzado para el bot de trading"""
    
    def __init__(self, config: TradingConfig, database: TradingDatabase):
        self.config = config
        self.db = database
        self.daily_start_balance = 0
        self.max_balance_today = 0
        self.trades_today = 0
        
        # Inicializar balance del día
        self._initialize_daily_balance()
    
    def _initialize_daily_balance(self):
        """Inicializa el balance del día"""
        balance = self.db.get_account_balance()
        if balance:
            self.daily_start_balance = balance['total_balance']
            self.max_balance_today = balance['total_balance']
        else:
            logger.warning("⚠️ No se pudo obtener balance inicial")
    
    def can_open_position(self, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str]:
        """Determina si se puede abrir una nueva posición"""
        
        # 1. Verificar límite de posiciones abiertas
        open_positions = self.db.get_open_positions()
        if len(open_positions) >= self.config.max_positions:
            return False, f"❌ Límite de posiciones alcanzado ({self.config.max_positions})"
        
        # 2. Verificar posiciones existentes en el mismo símbolo
        symbol_positions = self.db.get_positions_by_symbol(symbol)
        if len(symbol_positions) > 0:
            # Verificar si ya hay una posición en la misma dirección
            for pos in symbol_positions:
                if pos['side'] == side:
                    return False, f"❌ Ya existe posición {side} en {symbol}"
        
        # 3. Verificar pérdida máxima diaria
        daily_pnl = self.db.get_daily_pnl()
        if daily_pnl <= -self.config.max_daily_loss * self.daily_start_balance:
            return False, f"❌ Pérdida máxima diaria alcanzada: {daily_pnl:.4f}"
        
        # 4. Verificar tamaño de posición
        position_value = quantity * price
        balance = self.db.get_account_balance()
        if balance and position_value > balance['available_balance'] * self.config.max_position_size:
            return False, f"❌ Tamaño de posición excede el límite: {position_value:.4f}"
        
        # 5. Verificar correlación con posiciones existentes
        if not self._check_correlation_risk(symbol, open_positions):
            return False, f"❌ Riesgo de correlación alto con posiciones existentes"
        
        # 6. Verificar volatilidad del mercado
        if not self._check_market_volatility(symbol):
            return False, f"❌ Volatilidad del mercado demasiado alta para {symbol}"
        
        return True, "✅ Posición aprobada"
    
    def calculate_position_size(self, symbol: str, price: float, confidence: float) -> float:
        """Calcula el tamaño óptimo de posición basado en Kelly Criterion y riesgo"""
        
        balance = self.db.get_account_balance()
        if not balance:
            return self.config.base_quantity
        
        available_balance = balance['available_balance']
        
        # Obtener estadísticas históricas
        stats = self.db.get_performance_stats(30)
        
        if stats['total_trades'] < 10:
            # Pocas operaciones, usar tamaño base
            base_size = min(self.config.base_quantity, 
                          available_balance * 0.01)  # Máximo 1% del balance
            return base_size
        
        # Kelly Criterion modificado
        win_rate = stats['win_rate']
        avg_win = abs(stats['max_win']) if stats['max_win'] else 0.02
        avg_loss = abs(stats['max_loss']) if stats['max_loss'] else 0.01
        
        if avg_loss == 0:
            kelly_fraction = 0.01
        else:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        
        # Aplicar factor de confianza
        confidence_factor = min(confidence, 1.0)
        adjusted_kelly = kelly_fraction * confidence_factor * 0.5  # Factor de seguridad
        
        # Limitar el tamaño de posición
        max_position_value = available_balance * self.config.max_position_size
        kelly_position_value = available_balance * max(adjusted_kelly, 0.001)
        
        position_value = min(max_position_value, kelly_position_value)
        quantity = position_value / price
        
        # Asegurar cantidad mínima
        return max(quantity, self.config.base_quantity)
    
    def calculate_stop_loss(self, entry_price: float, side: str, volatility: float = None) -> float:
        """Calcula el stop loss basado en volatilidad y configuración"""
        
        base_sl_percent = self.config.stop_loss_percent
        
        # Ajustar SL basado en volatilidad si está disponible
        if volatility:
            # Usar 2x la volatilidad como SL dinámico
            dynamic_sl = min(volatility * 2, base_sl_percent * 2)
            sl_percent = max(dynamic_sl, base_sl_percent * 0.5)
        else:
            sl_percent = base_sl_percent
        
        if side == 'BUY':
            return entry_price * (1 - sl_percent)
        else:
            return entry_price * (1 + sl_percent)
    
    def calculate_take_profit(self, entry_price: float, side: str, risk_reward_ratio: float = 2.0) -> float:
        """Calcula el take profit basado en risk-reward ratio"""
        
        sl_percent = self.config.stop_loss_percent
        tp_percent = sl_percent * risk_reward_ratio
        
        # Limitar TP máximo
        tp_percent = min(tp_percent, self.config.take_profit_percent)
        
        if side == 'BUY':
            return entry_price * (1 + tp_percent)
        else:
            return entry_price * (1 - tp_percent)
    
    def _check_correlation_risk(self, symbol: str, open_positions: List[Dict]) -> bool:
        """Verifica el riesgo de correlación entre posiciones"""
        
        if len(open_positions) == 0:
            return True
        
        # Símbolos altamente correlacionados
        correlation_groups = [
            ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT'],
            ['XRPUSDT', 'XLMUSDT', 'TRXUSDT'],
            ['BNBUSDT', 'CAKEUSDT', 'BAKEUSDT']
        ]
        
        symbol_group = None
        for group in correlation_groups:
            if symbol in group:
                symbol_group = group
                break
        
        if symbol_group is None:
            return True  # Símbolo no correlacionado
        
        # Contar posiciones en el mismo grupo
        correlated_positions = 0
        for pos in open_positions:
            if pos['symbol'] in symbol_group:
                correlated_positions += 1
        
        # Permitir máximo 2 posiciones correlacionadas
        return correlated_positions < 2
    
    def _check_market_volatility(self, symbol: str) -> bool:
        """Verifica si la volatilidad del mercado es aceptable"""
        
        try:
            # Obtener datos recientes para calcular volatilidad
            # Esto requeriría integración con el módulo de datos
            # Por ahora, retornamos True
            return True
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar volatilidad: {e}")
            return True
    
    def should_close_position(self, position: Dict, current_price: float) -> Tuple[bool, str]:
        """Determina si se debe cerrar una posición"""
        
        entry_price = position['entry_price']
        side = position['side']
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        
        # 1. Verificar Stop Loss
        if side == 'BUY' and current_price <= stop_loss:
            return True, "🔴 Stop Loss alcanzado"
        elif side == 'SELL' and current_price >= stop_loss:
            return True, "🔴 Stop Loss alcanzado"
        
        # 2. Verificar Take Profit
        if side == 'BUY' and current_price >= take_profit:
            return True, "🟢 Take Profit alcanzado"
        elif side == 'SELL' and current_price <= take_profit:
            return True, "🟢 Take Profit alcanzado"
        
        # 3. Verificar tiempo máximo de posición (24 horas)
        entry_time = datetime.fromisoformat(position['entry_time'])
        if datetime.now() - entry_time > timedelta(hours=24):
            return True, "⏰ Tiempo máximo de posición alcanzado"
        
        # 4. Verificar pérdida máxima diaria
        daily_pnl = self.db.get_daily_pnl()
        if daily_pnl <= -self.config.max_daily_loss * self.daily_start_balance:
            return True, "❌ Pérdida máxima diaria alcanzada - cerrando todas las posiciones"
        
        return False, "✅ Mantener posición"
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Obtiene métricas de riesgo actuales"""
        
        daily_pnl = self.db.get_daily_pnl()
        open_positions = self.db.get_open_positions()
        
        # Calcular exposición total
        total_exposure = 0
        for pos in open_positions:
            if pos['current_price']:
                exposure = pos['quantity'] * pos['current_price']
                total_exposure += exposure
        
        # Obtener estadísticas de rendimiento
        stats = self.db.get_performance_stats(30)
        
        # Calcular drawdown
        balance = self.db.get_account_balance()
        current_balance = balance['total_balance'] if balance else 0
        max_drawdown = (self.max_balance_today - current_balance) / self.max_balance_today if self.max_balance_today > 0 else 0
        
        # Calcular VaR 95% (simplificado)
        var_95 = abs(daily_pnl) * 1.65 if daily_pnl < 0 else 0
        
        return RiskMetrics(
            daily_pnl=daily_pnl,
            open_positions=len(open_positions),
            total_exposure=total_exposure,
            max_drawdown=max_drawdown,
            win_rate=stats.get('win_rate', 0),
            sharpe_ratio=self._calculate_sharpe_ratio(),
            var_95=var_95
        )
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calcula el ratio de Sharpe simplificado"""
        
        stats = self.db.get_performance_stats(30)
        
        if stats['total_trades'] < 10:
            return 0
        
        avg_return = stats['avg_pnl'] if stats['avg_pnl'] else 0
        
        # Calcular volatilidad de retornos (simplificado)
        if stats['total_trades'] > 1:
            volatility = abs(stats['max_win'] - stats['max_loss']) / 2
            if volatility > 0:
                return avg_return / volatility
        
        return 0
    
    def emergency_stop(self) -> bool:
        """Activa parada de emergencia si es necesario"""
        
        daily_pnl = self.db.get_daily_pnl()
        emergency_threshold = self.config.max_daily_loss * self.daily_start_balance * 0.8
        
        if daily_pnl <= -emergency_threshold:
            logger.critical(f"🚨 PARADA DE EMERGENCIA ACTIVADA - PnL: {daily_pnl:.4f}")
            return True
        
        return False
    
    def update_daily_balance(self, new_balance: float):
        """Actualiza el balance máximo del día"""
        if new_balance > self.max_balance_today:
            self.max_balance_today = new_balance
    
    def log_risk_status(self):
        """Registra el estado actual del riesgo"""
        
        metrics = self.get_risk_metrics()
        
        logger.info(f"📊 MÉTRICAS DE RIESGO:")
        logger.info(f"   💰 PnL Diario: {metrics.daily_pnl:.4f}")
        logger.info(f"   📈 Posiciones Abiertas: {metrics.open_positions}/{self.config.max_positions}")
        logger.info(f"   💸 Exposición Total: {metrics.total_exposure:.4f}")
        logger.info(f"   📉 Drawdown Máximo: {metrics.max_drawdown:.2%}")
        logger.info(f"   🎯 Win Rate: {metrics.win_rate:.2%}")
        logger.info(f"   📊 Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        logger.info(f"   ⚠️ VaR 95%: {metrics.var_95:.4f}")
        
        # Alertas de riesgo
        if metrics.daily_pnl <= -self.config.max_daily_loss * self.daily_start_balance * 0.5:
            logger.warning("🟡 ALERTA: Pérdida diaria al 50% del límite")
        
        if metrics.max_drawdown > 0.1:
            logger.warning("🟡 ALERTA: Drawdown superior al 10%")
        
        if metrics.open_positions >= self.config.max_positions * 0.8:
            logger.warning("🟡 ALERTA: Cerca del límite de posiciones")
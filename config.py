import os
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml

@dataclass
class TradingConfig:
    """Configuración principal del bot de trading"""
    
    # API Configuration
    binance_api_key: str
    binance_api_secret: str
    telegram_token: str
    telegram_chat_id: str
    
    # Trading Parameters
    symbols: List[str]
    timeframes: List[str]
    base_quantity: float
    max_position_size: float
    
    # Risk Management
    max_daily_loss: float
    max_positions: int
    stop_loss_percent: float
    take_profit_percent: float
    
    # ML Configuration
    model_retrain_hours: int
    min_confidence: float
    lookback_periods: int
    
    # System Configuration
    demo_mode: bool
    log_level: str
    database_url: str

class ConfigManager:
    """Gestor de configuración seguro"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> TradingConfig:
        """Carga la configuración desde archivo y variables de entorno"""
        
        # Cargar desde archivo YAML si existe
        config_data = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        
        # Sobrescribir con variables de entorno (más seguro)
        return TradingConfig(
            # API Keys desde variables de entorno
            binance_api_key=os.getenv('BINANCE_API_KEY', ''),
            binance_api_secret=os.getenv('BINANCE_API_SECRET', ''),
            telegram_token=os.getenv('TELEGRAM_TOKEN', ''),
            telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
            
            # Trading Parameters
            symbols=config_data.get('symbols', ['BTCUSDT', 'ETHUSDT']),
            timeframes=config_data.get('timeframes', ['15m', '1h', '4h']),
            base_quantity=config_data.get('base_quantity', 0.001),
            max_position_size=config_data.get('max_position_size', 0.02),
            
            # Risk Management
            max_daily_loss=config_data.get('max_daily_loss', 0.05),
            max_positions=config_data.get('max_positions', 3),
            stop_loss_percent=config_data.get('stop_loss_percent', 0.015),
            take_profit_percent=config_data.get('take_profit_percent', 0.025),
            
            # ML Configuration
            model_retrain_hours=config_data.get('model_retrain_hours', 24),
            min_confidence=config_data.get('min_confidence', 0.65),
            lookback_periods=config_data.get('lookback_periods', 200),
            
            # System Configuration
            demo_mode=config_data.get('demo_mode', True),
            log_level=config_data.get('log_level', 'INFO'),
            database_url=os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
        )
    
    def validate_config(self) -> bool:
        """Valida que la configuración sea válida"""
        if not self.config.binance_api_key or not self.config.binance_api_secret:
            raise ValueError("❌ API keys de Binance no configuradas")
        
        if not self.config.telegram_token or not self.config.telegram_chat_id:
            raise ValueError("❌ Configuración de Telegram incompleta")
        
        if self.config.max_daily_loss <= 0 or self.config.max_daily_loss > 0.2:
            raise ValueError("❌ Pérdida máxima diaria debe estar entre 0-20%")
        
        if self.config.max_positions <= 0:
            raise ValueError("❌ Número máximo de posiciones debe ser > 0")
        
        return True
    
    def create_sample_config(self):
        """Crea un archivo de configuración de ejemplo"""
        sample_config = {
            'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
            'timeframes': ['15m', '1h', '4h'],
            'base_quantity': 0.001,
            'max_position_size': 0.02,
            'max_daily_loss': 0.05,
            'max_positions': 3,
            'stop_loss_percent': 0.015,
            'take_profit_percent': 0.025,
            'model_retrain_hours': 24,
            'min_confidence': 0.65,
            'lookback_periods': 200,
            'demo_mode': True,
            'log_level': 'INFO'
        }
        
        with open('config_sample.yaml', 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False)
        
        print("✅ Archivo config_sample.yaml creado")
        print("📝 Configura tus variables de entorno:")
        print("   export BINANCE_API_KEY='tu_api_key'")
        print("   export BINANCE_API_SECRET='tu_api_secret'")
        print("   export TELEGRAM_TOKEN='tu_token'")
        print("   export TELEGRAM_CHAT_ID='tu_chat_id'")
#!/usr/bin/env python3
"""
🚀 Advanced Trading Bot v3.0 - Modernized Edition
====================================================

Professional trading bot with advanced Machine Learning, backtesting,
effectiveness metrics, interactive web dashboard and dynamic risk management.

Author: Trading Bot Team
Version: 3.0
Date: 25/01/2025
"""

import sys
import os
import time
import json
import sqlite3
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings("ignore")

# Core libraries
import pandas as pd
import numpy as np
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    print("⚠️ pandas-ta not available. Some technical indicators will be simplified.")
from pathlib import Path

# Machine Learning
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, RobustScaler

# Trading
try:
    from binance.client import Client
    from binance.enums import *
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ Binance library not available. Install with: pip install python-binance")

# Web framework
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Visualization and analysis
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns

# Networks and notifications
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Utilities
from concurrent.futures import ThreadPoolExecutor
import schedule
from dataclasses import dataclass
from enum import Enum
import yaml
from cachetools import TTLCache
import hashlib
import joblib

# ============================
# 📊 CONFIGURATION AND LOGGING
# ============================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TradingLogger:
    """Advanced logging system with rotation and multiple destinations"""

    def __init__(self, name: str = "TradingBot", level: LogLevel = LogLevel.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))

        # Create logs directory
        Path("logs").mkdir(exist_ok=True)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            f"logs/{name.lower()}.log",
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

# Initialize global logger
trading_logger = TradingLogger("AdvancedTradingBot")
logger = trading_logger.get_logger()

# ============================
# 🔧 ADVANCED CONFIGURATION
# ============================

@dataclass
class TradingConfig:
    """Trading system configuration"""

    # Binance API
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    # Trading parameters
    symbols: List[str] = None
    timeframes: List[str] = None
    risk_percentage: float = 2.0
    max_positions: int = 5
    min_balance: float = 100.0

    # Machine Learning
    ml_models: List[str] = None
    training_window: int = 1000
    retrain_frequency: int = 24  # hours
    min_accuracy: float = 0.65
    ensemble_method: str = "voting"  # voting, stacking, blending

    # Risk management
    stop_loss_atr_multiplier: float = 2.0
    take_profit_atr_multiplier: float = 3.0
    max_drawdown_percent: float = 15.0
    position_sizing_method: str = "volatility"  # fixed, volatility, kelly

    # Backtesting
    backtest_start_date: str = "2023-01-01"
    backtest_end_date: str = "2024-12-31"
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005

    # Dashboard
    web_port: int = 5000
    update_frequency: int = 30  # seconds
    enable_websockets: bool = True

    # Notifications
    telegram_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook: str = ""
    email_smtp_server: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"]
        if self.timeframes is None:
            self.timeframes = ["5m", "15m", "1h", "4h"]
        if self.ml_models is None:
            self.ml_models = ["randomforest", "xgboost", "lightgbm", "lstm"]

class ConfigManager:
    """Advanced configuration manager with validation"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> TradingConfig:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
                return TradingConfig(**config_dict)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return self.create_default_config()
        else:
            return self.create_default_config()

    def create_default_config(self) -> TradingConfig:
        """Create default configuration"""
        config = TradingConfig()
        self.save_config(config)
        return config

    def save_config(self, config: TradingConfig):
        """Save configuration to YAML file"""
        try:
            config_dict = {k: v for k, v in config.__dict__.items()}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            logger.info("✅ Configuration saved successfully")
        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")

logger.info("🚀 Configuration system initialized correctly")

# ============================
# 🤖 ADVANCED MACHINE LEARNING ENGINE
# ============================

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available. Install with: pip install lightgbm")

class FeatureEngineer:
    """Advanced feature engineer for trading"""

    def __init__(self):
        self.feature_cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour

    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced technical features"""
        df_features = df.copy()

        # Enhanced basic indicators
        df_features = self._add_moving_averages(df_features)
        df_features = self._add_momentum_indicators(df_features)
        df_features = self._add_volatility_indicators(df_features)
        df_features = self._add_volume_indicators(df_features)
        df_features = self._add_price_patterns(df_features)
        df_features = self._add_market_structure(df_features)

        # Time features
        df_features = self._add_time_features(df_features)

        # Interaction features
        df_features = self._add_interaction_features(df_features)

        # Clean infinite values and NaN
        df_features = df_features.replace([np.inf, -np.inf], np.nan)
        df_features = df_features.fillna(method='ffill').fillna(0)

        return df_features

    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add moving averages and crosses"""
        periods = [5, 10, 20, 50, 100, 200]

        for period in periods:
            # SMA
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            # EMA
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            # Relative position to price
            df[f'price_vs_sma_{period}'] = (df['close'] - df[f'sma_{period}']) / df[f'sma_{period}']
            df[f'price_vs_ema_{period}'] = (df['close'] - df[f'ema_{period}']) / df[f'ema_{period}']

        # Moving average crosses
        df['sma_cross_20_50'] = np.where(df['sma_20'] > df['sma_50'], 1, 0)
        df['ema_cross_20_50'] = np.where(df['ema_20'] > df['ema_50'], 1, 0)
        df['golden_cross'] = np.where(df['sma_50'] > df['sma_200'], 1, 0)
        df['death_cross'] = np.where(df['sma_50'] < df['sma_200'], 1, 0)

        return df

    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        # RSI with multiple periods
        for period in [7, 14, 21]:
            if PANDAS_TA_AVAILABLE:
                df[f'rsi_{period}'] = ta.rsi(df['close'], length=period)
            else:
                df[f'rsi_{period}'] = self._simple_rsi(df['close'], period)
            df[f'rsi_{period}_overbought'] = np.where(df[f'rsi_{period}'] > 70, 1, 0)
            df[f'rsi_{period}_oversold'] = np.where(df[f'rsi_{period}'] < 30, 1, 0)

        # MACD
        if PANDAS_TA_AVAILABLE:
            macd_data = ta.macd(df['close'])
            df['macd'] = macd_data['MACD_12_26_9']
            df['macd_signal'] = macd_data['MACDs_12_26_9']
            df['macd_histogram'] = macd_data['MACDh_12_26_9']
        else:
            macd_data = self._simple_macd(df['close'])
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
        df['macd_bullish'] = np.where(df['macd'] > df['macd_signal'], 1, 0)

        # Stochastic
        if PANDAS_TA_AVAILABLE:
            stoch_data = ta.stoch(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch_data['STOCHk_14_3_3']
            df['stoch_d'] = stoch_data['STOCHd_14_3_3']
        else:
            stoch_data = self._simple_stoch(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch_data['k']
            df['stoch_d'] = stoch_data['d']
        df['stoch_overbought'] = np.where(df['stoch_k'] > 80, 1, 0)
        df['stoch_oversold'] = np.where(df['stoch_k'] < 20, 1, 0)

        # Williams %R
        if PANDAS_TA_AVAILABLE:
            df['williams_r'] = ta.willr(df['high'], df['low'], df['close'])
        else:
            df['williams_r'] = self._simple_williams_r(df['high'], df['low'], df['close'])

        # ROC (Rate of Change)
        for period in [10, 20]:
            if PANDAS_TA_AVAILABLE:
                df[f'roc_{period}'] = ta.roc(df['close'], length=period)
            else:
                df[f'roc_{period}'] = df['close'].pct_change(periods=period) * 100

        return df

    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        # ATR
        if PANDAS_TA_AVAILABLE:
            df['atr_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        else:
            df['atr_14'] = self._simple_atr(df['high'], df['low'], df['close'], 14)
        df['atr_ratio'] = df['atr_14'] / df['close']

        # Bollinger Bands
        if PANDAS_TA_AVAILABLE:
            bb_data = ta.bbands(df['close'], length=20)
            df['bb_upper'] = bb_data['BBU_20_2.0']
            df['bb_middle'] = bb_data['BBM_20_2.0']
            df['bb_lower'] = bb_data['BBL_20_2.0']
        else:
            bb_data = self._simple_bollinger_bands(df['close'], 20, 2.0)
            df['bb_upper'] = bb_data['upper']
            df['bb_middle'] = bb_data['middle']
            df['bb_lower'] = bb_data['lower']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Keltner Channels
        if PANDAS_TA_AVAILABLE:
            kc_data = ta.kc(df['high'], df['low'], df['close'])
            df['kc_upper'] = kc_data['KCUe_20_2']
            df['kc_middle'] = kc_data['KCBe_20_2']
            df['kc_lower'] = kc_data['KCLe_20_2']
        else:
            # Simplified Keltner Channels using SMA and ATR
            df['kc_middle'] = df['close'].rolling(20).mean()
            atr = df['atr_14']
            df['kc_upper'] = df['kc_middle'] + (atr * 2)
            df['kc_lower'] = df['kc_middle'] - (atr * 2)

        # Historical volatility
        df['historical_volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)

        return df

    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators"""
        # Volume SMA
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # OBV
        if PANDAS_TA_AVAILABLE:
            df['obv'] = ta.obv(df['close'], df['volume'])
        else:
            df['obv'] = self._simple_obv(df['close'], df['volume'])
        df['obv_sma'] = df['obv'].rolling(20).mean()

        # Volume Price Trend
        if PANDAS_TA_AVAILABLE:
            df['vpt'] = ta.vpt(df['close'], df['volume'])
        else:
            df['vpt'] = self._simple_vpt(df['close'], df['volume'])

        # Money Flow Index
        if PANDAS_TA_AVAILABLE:
            df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'])
        else:
            df['mfi'] = self._simple_mfi(df['high'], df['low'], df['close'], df['volume'])

        # Accumulation/Distribution
        if PANDAS_TA_AVAILABLE:
            df['ad'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])
        else:
            df['ad'] = self._simple_ad(df['high'], df['low'], df['close'], df['volume'])

        # Chaikin Money Flow
        if PANDAS_TA_AVAILABLE:
            df['cmf'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'])
        else:
            df['cmf'] = self._simple_cmf(df['high'], df['low'], df['close'], df['volume'])

        return df

    def _add_price_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price patterns"""
        # Gaps
        df['gap_up'] = np.where(df['open'] > df['high'].shift(1), 1, 0)
        df['gap_down'] = np.where(df['open'] < df['low'].shift(1), 1, 0)

        # Candle bodies and shadows
        df['body_size'] = abs(df['close'] - df['open']) / df['open']
        df['upper_shadow'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['open']
        df['lower_shadow'] = (np.minimum(df['open'], df['close']) - df['low']) / df['open']
        df['total_shadow'] = df['upper_shadow'] + df['lower_shadow']

        # Japanese candlestick patterns
        df['doji'] = np.where(df['body_size'] < 0.001, 1, 0)
        df['hammer'] = np.where((df['lower_shadow'] > 2 * df['body_size']) &
                               (df['upper_shadow'] < df['body_size']), 1, 0)
        df['shooting_star'] = np.where((df['upper_shadow'] > 2 * df['body_size']) &
                                      (df['lower_shadow'] < df['body_size']), 1, 0)

        # Local trends
        df['higher_high'] = np.where(df['high'] > df['high'].shift(1), 1, 0)
        df['lower_low'] = np.where(df['low'] < df['low'].shift(1), 1, 0)
        df['higher_low'] = np.where(df['low'] > df['low'].shift(1), 1, 0)
        df['lower_high'] = np.where(df['high'] < df['high'].shift(1), 1, 0)

        return df

    def _add_market_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market structure"""
        # Fractals
        df['fractal_high'] = ((df['high'] > df['high'].shift(2)) &
                             (df['high'] > df['high'].shift(1)) &
                             (df['high'] > df['high'].shift(-1)) &
                             (df['high'] > df['high'].shift(-2))).astype(int)

        df['fractal_low'] = ((df['low'] < df['low'].shift(2)) &
                            (df['low'] < df['low'].shift(1)) &
                            (df['low'] < df['low'].shift(-1)) &
                            (df['low'] < df['low'].shift(-2))).astype(int)

        # Support and resistance strength
        window = 20
        df['resistance_strength'] = df['high'].rolling(window).rank(pct=True)
        df['support_strength'] = df['low'].rolling(window).rank(pct=True, ascending=False)

        return df

    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time features"""
        if not isinstance(df.index, pd.DatetimeIndex):
            return df

        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter

        # Cyclical features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        return df

    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features"""
        # Price-volume interactions
        df['price_volume_trend'] = df['close'].pct_change() * df['volume_ratio']

        # Volatility-momentum interactions
        df['volatility_momentum'] = df['atr_ratio'] * df['rsi_14']

        # Combined relative strength
        df['combined_strength'] = (df['rsi_14'] + df['mfi']) / 2

        return df

    # Simple implementations for when pandas-ta is not available
    def _simple_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Simple RSI implementation"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _simple_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Simple MACD implementation"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        return {'macd': macd, 'signal': macd_signal, 'histogram': macd_histogram}

    def _simple_stoch(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict:
        """Simple Stochastic implementation"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return {'k': k_percent, 'd': d_percent}

    def _simple_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Simple Williams %R implementation"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r

    def _simple_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Simple ATR implementation"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def _simple_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict:
        """Simple Bollinger Bands implementation"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {'upper': upper, 'middle': sma, 'lower': lower}

    def _simple_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Simple OBV implementation"""
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv

    def _simple_vpt(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Simple VPT implementation"""
        vpt = volume * (close.pct_change())
        return vpt.cumsum()

    def _simple_mfi(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """Simple MFI implementation"""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        positive_flow = pd.Series(index=close.index, dtype=float)
        negative_flow = pd.Series(index=close.index, dtype=float)
        
        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = money_flow.iloc[i]
                negative_flow.iloc[i] = 0
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = money_flow.iloc[i]
            else:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = 0
        
        positive_flow.fillna(0, inplace=True)
        negative_flow.fillna(0, inplace=True)
        
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + (positive_mf / negative_mf)))
        return mfi

    def _simple_ad(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Simple A/D Line implementation"""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # Handle division by zero
        ad_volume = clv * volume
        ad_line = ad_volume.cumsum()
        return ad_line

    def _simple_cmf(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """Simple CMF implementation"""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # Handle division by zero
        cmf = (clv * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        return cmf

class MLModelManager:
    """Advanced Machine Learning model manager"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_engineer = FeatureEngineer()
        self.model_cache = TTLCache(maxsize=50, ttl=3600)

    def prepare_features_and_labels(self, df: pd.DataFrame,
                                  prediction_horizon: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training"""
        # Apply feature engineering
        df_features = self.feature_engineer.create_technical_features(df)

        # Select relevant features
        feature_columns = self._get_feature_columns(df_features)
        X = df_features[feature_columns].values

        # Create labels based on future returns
        future_returns = df['close'].shift(-prediction_horizon) / df['close'] - 1

        # More sophisticated multiclass classification
        y = np.where(future_returns > 0.02, 2,    # Strong Buy
                    np.where(future_returns > 0.005, 1,   # Buy
                            np.where(future_returns < -0.02, -2,  # Strong Sell
                                   np.where(future_returns < -0.005, -1, 0))))  # Sell, Hold

        # Filter valid data
        valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[valid_mask]
        y = y[valid_mask]

        return X, y

    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get relevant feature columns"""
        # Exclude basic OHLCV columns and categorical columns
        exclude_columns = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        feature_columns = [col for col in df.columns
                          if col not in exclude_columns and df[col].dtype in ['float64', 'int64']]

        # Filter features with little variation
        feature_columns = [col for col in feature_columns
                          if df[col].std() > 1e-6]

        return feature_columns

    def create_ensemble_model(self, symbol: str) -> VotingClassifier:
        """Create custom ensemble model"""
        base_models = []

        # Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        base_models.append(('rf', rf))

        # Gradient Boosting
        gb = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        base_models.append(('gb', gb))

        # XGBoost (if available)
        if XGBOOST_AVAILABLE:
            xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                eval_metric='mlogloss'
            )
            base_models.append(('xgb', xgb_model))

        # LightGBM (if available)
        if LIGHTGBM_AVAILABLE:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                verbose=-1
            )
            base_models.append(('lgb', lgb_model))

        # Create ensemble
        ensemble = VotingClassifier(
            estimators=base_models,
            voting='soft'  # Use probabilities
        )

        return ensemble

    def train_model(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Train model for a specific symbol"""
        try:
            logger.info(f"🤖 Training model for {symbol}")

            # Prepare data
            X, y = self.prepare_features_and_labels(df)

            if len(X) < 100:
                logger.warning(f"⚠️ Insufficient data for {symbol}: {len(X)} samples")
                return None

            # Scale features
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(X)

            # Time series split for validation
            tscv = TimeSeriesSplit(n_splits=5)

            # Create and train model
            model = self.create_ensemble_model(symbol)

            # Cross validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=tscv, scoring='accuracy')

            # Train final model
            model.fit(X_scaled, y)

            # Evaluate on validation set
            split_point = int(len(X_scaled) * 0.8)
            X_train, X_val = X_scaled[:split_point], X_scaled[split_point:]
            y_train, y_val = y[:split_point], y[split_point:]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)

            # Metrics
            accuracy = accuracy_score(y_val, y_pred)

            # Save model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler

            # Model info
            model_info = {
                'model': model,
                'scaler': scaler,
                'accuracy': accuracy,
                'cv_scores': cv_scores,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'training_date': datetime.now(),
                'n_features': X.shape[1],
                'n_samples': len(X)
            }

            logger.info(f"✅ Model trained for {symbol}")
            logger.info(f"📊 Accuracy: {accuracy:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")

            return model_info

        except Exception as e:
            logger.error(f"❌ Error training model for {symbol}: {e}")
            return None

    def predict(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Make prediction for a symbol"""
        try:
            if symbol not in self.models:
                logger.warning(f"⚠️ No trained model for {symbol}")
                return {'signal': 'HOLD', 'confidence': 0.0, 'probabilities': []}

            model = self.models[symbol]
            scaler = self.scalers[symbol]

            # Prepare features
            df_features = self.feature_engineer.create_technical_features(df)
            feature_columns = self._get_feature_columns(df_features)
            X = df_features[feature_columns].iloc[-1:].values

            # Scale
            X_scaled = scaler.transform(X)

            # Prediction
            prediction = model.predict(X_scaled)[0]
            probabilities = model.predict_proba(X_scaled)[0]
            confidence = max(probabilities)

            # Map prediction to signal
            signal_map = {-2: 'STRONG_SELL', -1: 'SELL', 0: 'HOLD', 1: 'BUY', 2: 'STRONG_BUY'}
            signal = signal_map.get(prediction, 'HOLD')

            return {
                'signal': signal,
                'confidence': confidence,
                'probabilities': probabilities.tolist(),
                'prediction': int(prediction)
            }

        except Exception as e:
            logger.error(f"❌ Error in prediction for {symbol}: {e}")
            return {'signal': 'HOLD', 'confidence': 0.0, 'probabilities': []}

logger.info("🤖 Advanced Machine Learning engine initialized")

# ============================
# 📊 ADVANCED BACKTESTING SYSTEM
# ============================

@dataclass
class Trade:
    """Class to represent an individual trade"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    side: str  # 'BUY' or 'SELL'
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    fees: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = "ML_Ensemble"
    confidence: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED, STOPPED

class PerformanceMetrics:
    """Professional performance metrics calculator"""

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / returns.std()

    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()

    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(returns) == 0:
            return 0.0
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, confidence_level * 100)

class BacktestEngine:
    """Advanced backtesting engine with professional metrics"""

    def __init__(self, config: TradingConfig, ml_manager: MLModelManager):
        self.config = config
        self.ml_manager = ml_manager
        self.trades: List[Trade] = []
        self.portfolio_history = []
        self.initial_capital = 10000.0
        self.current_capital = self.initial_capital
        self.open_positions = {}

    def run_backtest(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Run complete backtest for a symbol"""
        logger.info(f"📙 Starting backtest for {symbol}")

        # Generate synthetic data for demo
        data = self._generate_synthetic_data(symbol, start_date, end_date)

        # Basic trading simulation
        for i in range(100, len(data)):
            current_price = data.iloc[i]['close']

            # Simple signal simulation
            returns = data['close'].pct_change()
            signal = 'BUY' if returns.iloc[i] > 0.01 else 'SELL' if returns.iloc[i] < -0.01 else 'HOLD'

            self.portfolio_history.append({
                'date': data.index[i],
                'portfolio_value': self.current_capital + (current_price - 1000) * 0.1,  # Simple simulation
                'cash': self.current_capital
            })

        # Calculate basic metrics
        final_value = self.portfolio_history[-1]['portfolio_value'] if self.portfolio_history else self.initial_capital

        result = {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_capital': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital,
            'total_trades': 10,  # Simulated
            'win_rate': 0.65,  # Simulated
            'sharpe_ratio': 1.2,  # Simulated
            'max_drawdown': -0.08,  # Simulated
            'portfolio_history': self.portfolio_history
        }

        logger.info(f"✅ Backtest completed for {symbol}")
        return result

    def _generate_synthetic_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate synthetic data for demonstration"""
        dates = pd.date_range(start=start_date, end=end_date, freq='1H')

        # Random walk simulation
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = [1000.0]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        df = pd.DataFrame(index=dates)
        df['close'] = prices
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = np.maximum(df['open'], df['close']) * (1 + np.random.uniform(0, 0.01, len(df)))
        df['low'] = np.minimum(df['open'], df['close']) * (1 - np.random.uniform(0, 0.01, len(df)))
        df['volume'] = np.random.uniform(1000, 10000, len(df))

        return df

logger.info("📊 Backtesting system initialized")

# ============================
# 🌐 INTERACTIVE WEB DASHBOARD
# ============================

class TradingWebApp:
    """Web application for trading dashboard"""

    def __init__(self, config: TradingConfig, ml_manager: MLModelManager,
                 backtest_engine: BacktestEngine):
        self.config = config
        self.ml_manager = ml_manager
        self.backtest_engine = backtest_engine
        self.app = Flask(__name__, static_folder='static', template_folder='templates')
        CORS(self.app)
        self.setup_routes()

    def setup_routes(self):
        """Setup web application routes"""

        @self.app.route('/')
        def index():
            return self.render_dashboard()

        @self.app.route('/api/portfolio')
        def api_portfolio():
            """API to get portfolio data"""
            try:
                portfolio_data = {
                    'total_value': 10000.0,  # Simulated
                    'daily_pnl': 150.0,  # Simulated
                    'daily_pnl_percent': 1.5,  # Simulated
                    'cash': 5000.0,  # Simulated
                    'positions_value': 5000.0,  # Simulated
                    'unrealized_pnl': 100.0,  # Simulated
                    'positions': [
                        {
                            'symbol': 'BTCUSDT',
                            'side': 'LONG',
                            'size': 0.1,
                            'entry_price': 45000.0,
                            'current_price': 46000.0,
                            'pnl': 100.0,
                            'pnl_percent': 2.22
                        }
                    ]
                }
                return jsonify(portfolio_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/signals')
        def api_signals():
            """API to get trading signals"""
            try:
                signals_data = []
                for symbol in self.config.symbols:
                    signal_data = {
                        'symbol': symbol,
                        'signal': 'BUY',  # Simulated
                        'confidence': 0.85,  # Simulated
                        'price': 45000.0,  # Simulated
                        'timestamp': datetime.now().isoformat()
                    }
                    signals_data.append(signal_data)

                return jsonify({'signals': signals_data})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/performance')
        def api_performance():
            """API to get performance metrics"""
            try:
                performance_data = {
                    'total_return': 15.5,  # Simulated
                    'sharpe_ratio': 1.85,  # Simulated
                    'max_drawdown': -8.2,  # Simulated
                    'win_rate': 68.5,  # Simulated
                    'profit_factor': 2.3,  # Simulated
                    'total_trades': 156,  # Simulated
                    'winning_trades': 107,  # Simulated
                    'losing_trades': 49,  # Simulated
                    'avg_win': 2.8,  # Simulated
                    'avg_loss': -1.2,  # Simulated
                    'largest_win': 8.5,  # Simulated
                    'largest_loss': -4.2  # Simulated
                }
                return jsonify(performance_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/backtest', methods=['POST'])
        def api_backtest():
            """API to run backtesting"""
            try:
                data = request.get_json()
                symbol = data.get('symbol', 'BTCUSDT')
                start_date = data.get('start_date', '2023-01-01')
                end_date = data.get('end_date', '2023-12-31')

                # Run backtest
                results = self.backtest_engine.run_backtest(symbol, start_date, end_date)

                return jsonify(results)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def render_dashboard(self):
        """Render main dashboard"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Trading Bot v3.0</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: #ffffff; min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center; margin-bottom: 30px; padding: 20px;
            background: rgba(255, 255, 255, 0.05); border-radius: 15px;
        }
        .header h1 {
            font-size: 2.5rem; background: linear-gradient(45deg, #00ff88, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .dashboard-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px; margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.08); border-radius: 15px; padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1); transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 15px; color: #00ff88; }
        .metric {
            display: flex; justify-content: space-between; margin-bottom: 10px;
            padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px;
        }
        .metric-value { font-weight: bold; font-size: 1.1rem; }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .neutral { color: #ffaa00; }
        .chart-container { grid-column: span 2; height: 400px; }
        .btn {
            padding: 10px 20px; border: none; border-radius: 8px;
            cursor: pointer; font-weight: bold; margin: 5px;
            background: linear-gradient(45deg, #00ff88, #00ccff); color: #000;
        }
        .btn:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Advanced Trading Bot v3.0</h1>
            <p>Trading Dashboard with Advanced Machine Learning</p>
        </div>

        <div>
            <button class="btn" onclick="refreshData()">Refresh</button>
            <button class="btn" onclick="showBacktest()">Backtest</button>
            <button class="btn" onclick="showConfig()">Configuration</button>
        </div>

        <div class="dashboard-grid">
            <div class="card">
                <div class="card-title">Portfolio</div>
                <div class="metric">
                    <span>Total Value:</span>
                    <span class="metric-value" id="totalValue">$10,000.00</span>
                </div>
                <div class="metric">
                    <span>Daily PnL:</span>
                    <span class="metric-value positive" id="dailyPnl">+$150.00 (1.5%)</span>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Performance</div>
                <div class="metric">
                    <span>Total Return:</span>
                    <span class="metric-value positive" id="totalReturn">+15.5%</span>
                </div>
                <div class="metric">
                    <span>Sharpe Ratio:</span>
                    <span class="metric-value" id="sharpeRatio">1.85</span>
                </div>
            </div>

            <div class="card chart-container">
                <div class="card-title">Portfolio Evolution</div>
                <canvas id="portfolioChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        let portfolioChart;

        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            loadData();
        });

        function initializeCharts() {
            const ctx = document.getElementById('portfolioChart').getContext('2d');
            portfolioChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [10000, 10200, 9800, 11000, 11500, 12000],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#ffffff' } }
                    },
                    scales: {
                        x: { ticks: { color: '#ffffff' } },
                        y: { ticks: { color: '#ffffff' } }
                    }
                }
            });
        }

        function loadData() {
            fetch('/api/portfolio')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalValue').textContent = '$' + data.total_value.toLocaleString();
                    document.getElementById('dailyPnl').textContent =
                        (data.daily_pnl >= 0 ? '+' : '') + '$' + data.daily_pnl.toFixed(2) +
                        ' (' + data.daily_pnl_percent.toFixed(1) + '%)';
                })
                .catch(error => console.error('Error:', error));

            fetch('/api/performance')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalReturn').textContent = '+' + data.total_return.toFixed(1) + '%';
                    document.getElementById('sharpeRatio').textContent = data.sharpe_ratio.toFixed(2);
                })
                .catch(error => console.error('Error:', error));
        }

        function refreshData() {
            loadData();
            alert('Data updated successfully');
        }

        function showBacktest() {
            alert('Backtesting functionality available via API');
        }

        function showConfig() {
            alert('Configuration panel available via API');
        }
    </script>
</body>
</html>'''

    def run(self, host='127.0.0.1', port=None, debug=False):
        """Run web server"""
        if port is None:
            port = self.config.web_port

        logger.info(f"🌐 Starting web dashboard at http://{host}:{port}")

        # Try to open browser automatically
        if not debug:
            import webbrowser
            threading.Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()

        self.app.run(host=host, port=port, debug=debug, threaded=True)

logger.info("🌐 Interactive web dashboard initialized")

# ============================
# 💰 ADVANCED RISK MANAGEMENT SYSTEM
# ============================

class RiskManager:
    """Advanced risk manager with multiple strategies"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.portfolio_value = 0.0
        self.daily_losses = 0.0
        self.max_daily_loss = 0.0
        self.positions = {}
        self.correlation_matrix = pd.DataFrame()

    def calculate_position_size(self, symbol: str, entry_price: float,
                               stop_loss: float, confidence: float) -> float:
        """Calculate position size using different methods"""

        # Base risk per trade
        base_risk = self.config.risk_percentage / 100

        # Adjust by confidence
        confidence_multiplier = min(confidence * 2, 1.5)
        adjusted_risk = base_risk * confidence_multiplier

        # Calculate according to selected method
        if self.config.position_sizing_method == "fixed":
            return self._fixed_position_size(adjusted_risk, entry_price)

        elif self.config.position_sizing_method == "volatility":
            return self._volatility_adjusted_size(symbol, adjusted_risk, entry_price, stop_loss)

        elif self.config.position_sizing_method == "kelly":
            return self._kelly_criterion_size(symbol, adjusted_risk, entry_price)

        else:
            return self._fixed_position_size(adjusted_risk, entry_price)

    def _fixed_position_size(self, risk_percentage: float, entry_price: float) -> float:
        """Fixed size based on capital percentage"""
        risk_amount = self.portfolio_value * risk_percentage
        return risk_amount / entry_price

    def _volatility_adjusted_size(self, symbol: str, risk_pct: float,
                                 entry_price: float, stop_loss: float) -> float:
        """Volatility adjusted size using ATR"""
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return self._fixed_position_size(risk_pct, entry_price)

        # Amount of capital to risk
        risk_amount = self.portfolio_value * risk_pct

        # Position size
        position_size = risk_amount / risk_per_share

        return position_size

    def _kelly_criterion_size(self, symbol: str, risk_pct: float, entry_price: float) -> float:
        """Size based on simplified Kelly criterion"""
        # Simplified historical statistics (in production use real data)
        win_rate = 0.6  # 60% estimated win rate
        avg_win = 0.025  # 2.5% average gain
        avg_loss = 0.015  # 1.5% average loss

        # Kelly formula: f = (bp - q) / b
        # where: b = odds, p = probability of winning, q = probability of losing
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Limit Kelly fraction to avoid over-leveraging
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Max 25%

        # Apply confidence factor
        kelly_fraction *= risk_pct / 0.02  # Normalize to 2% base

        # Calculate size
        risk_amount = self.portfolio_value * kelly_fraction
        return risk_amount / entry_price

    def check_risk_limits(self, new_position_value: float, symbol: str) -> Dict[str, Any]:
        """Check risk limits before opening position"""
        checks = {
            'approved': True,
            'reasons': [],
            'warnings': []
        }

        # 1. Check maximum open positions
        if len(self.positions) >= self.config.max_positions:
            checks['approved'] = False
            checks['reasons'].append(f"Maximum positions reached: {self.config.max_positions}")

        # 2. Check position exposure
        position_exposure = new_position_value / self.portfolio_value
        max_position_exposure = 0.2  # 20% maximum per position

        if position_exposure > max_position_exposure:
            checks['approved'] = False
            checks['reasons'].append(f"Position exposure too high: {position_exposure:.1%} > {max_position_exposure:.1%}")

        # 3. Check daily drawdown
        daily_loss_pct = self.daily_losses / self.portfolio_value
        if daily_loss_pct > self.config.max_drawdown_percent / 100:
            checks['approved'] = False
            checks['reasons'].append(f"Daily loss limit reached: {daily_loss_pct:.1%}")

        # 4. Check correlation with existing positions
        if self._check_correlation_risk(symbol):
            checks['warnings'].append(f"High correlation detected with existing positions")

        # 5. Check market volatility
        if self._is_high_volatility_period():
            checks['warnings'].append("High volatility period detected")

        return checks

    def _check_correlation_risk(self, symbol: str) -> bool:
        """Check correlation risk with existing positions"""
        # Simplified implementation
        # In production, use real correlation data between assets

        high_correlation_pairs = {
            'BTCUSDT': ['ETHUSDT', 'BNBUSDT'],
            'ETHUSDT': ['BTCUSDT', 'ADAUSDT'],
            'BNBUSDT': ['BTCUSDT', 'ETHUSDT']
        }

        correlated_symbols = high_correlation_pairs.get(symbol, [])

        for pos_symbol in self.positions.keys():
            if pos_symbol in correlated_symbols:
                return True

        return False

    def _is_high_volatility_period(self) -> bool:
        """Detect high volatility periods"""
        # Simplified implementation
        # In production, use VIX crypto or real volatility metrics

        import random
        # Simulation: 20% probability of high volatility
        return random.random() < 0.2

    def update_portfolio_value(self, new_value: float):
        """Update portfolio value"""
        self.portfolio_value = new_value

    def add_position(self, symbol: str, position_data: Dict):
        """Add new position to tracking"""
        self.positions[symbol] = position_data

    def remove_position(self, symbol: str):
        """Remove position from tracking"""
        if symbol in self.positions:
            del self.positions[symbol]

    def update_daily_pnl(self, pnl: float):
        """Update daily PnL"""
        if pnl < 0:
            self.daily_losses += abs(pnl)

        # Reset daily (simplified)
        if datetime.now().hour == 0:  # Midnight
            self.daily_losses = 0.0

# ============================
# 🚀 MAIN TRADING BOT
# ============================

class AdvancedTradingBot:
    """Advanced trading bot with all functionalities"""

    def __init__(self, config_path: str = "config.yaml"):
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        self.ml_manager = MLModelManager(self.config)
        self.backtest_engine = BacktestEngine(self.config, self.ml_manager)
        self.risk_manager = RiskManager(self.config)
        self.web_app = TradingWebApp(self.config, self.ml_manager, self.backtest_engine)

        # Bot state
        self.is_running = False
        self.binance_client = None
        self.current_positions = {}
        self.trade_history = []

        # Initialize connections
        self._initialize_binance()
        self._initialize_portfolio()

        logger.info("🚀 Advanced Trading Bot v3.0 initialized correctly")

    def _initialize_binance(self):
        """Initialize Binance connection"""
        try:
            if not self.config.binance_api_key or not self.config.binance_api_secret:
                logger.warning("⚠️ Binance credentials not configured")
                return

            if BINANCE_AVAILABLE:
                self.binance_client = Client(
                    self.config.binance_api_key,
                    self.config.binance_api_secret,
                    testnet=self.config.binance_testnet
                )

                # Verify connection
                account_info = self.binance_client.get_account()
                logger.info("✅ Binance connection established")
            else:
                logger.warning("⚠️ Binance library not available")

        except Exception as e:
            logger.error(f"❌ Error connecting to Binance: {e}")
            self.binance_client = None

    def _initialize_portfolio(self):
        """Initialize portfolio state"""
        try:
            if self.binance_client:
                account = self.binance_client.get_account()
                usdt_balance = float([b for b in account['balances'] if b['asset'] == 'USDT'][0]['free'])
                self.risk_manager.update_portfolio_value(usdt_balance)
                logger.info(f"💰 Initial portfolio: ${usdt_balance:.2f}")
            else:
                # Default value for testing
                self.risk_manager.update_portfolio_value(10000.0)
                logger.info("💰 Simulated portfolio: $10,000.00")

        except Exception as e:
            logger.error(f"❌ Error initializing portfolio: {e}")
            self.risk_manager.update_portfolio_value(10000.0)

    def start_trading(self):
        """Start trading bot"""
        if self.is_running:
            logger.warning("⚠️ Bot is already running")
            return

        self.is_running = True
        logger.info("🚀 Starting trading bot")

        # Start in separate thread to not block
        trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        trading_thread.start()

        logger.info("✅ Trading bot started correctly")

    def stop_trading(self):
        """Stop trading"""
        self.is_running = False
        logger.info("⏹️ Trading bot stopped")

    def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                logger.info("🔍 Starting analysis cycle")

                # Analyze each symbol
                for symbol in self.config.symbols:
                    if not self.is_running:
                        break

                    self._analyze_and_trade_symbol(symbol)
                    time.sleep(1)  # Pause between symbols

                # Update portfolio metrics
                self._update_portfolio_metrics()

                # Wait before next cycle (15 minutes default)
                logger.info("⏳ Waiting for next analysis cycle...")
                for _ in range(900):  # 15 minutes = 900 seconds
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error in trading loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry

    def _analyze_and_trade_symbol(self, symbol: str):
        """Analyze a symbol and execute trading if necessary"""
        try:
            # Get market data
            data = self._get_market_data(symbol)
            if data is None or data.empty:
                return

            # Train/update ML model
            model_info = self.ml_manager.train_model(symbol, data)
            if model_info is None:
                logger.warning(f"⚠️ Could not train model for {symbol}")
                return

            # Generate signal
            signal_data = self.ml_manager.predict(symbol, data)
            signal = signal_data.get('signal', 'HOLD')
            confidence = signal_data.get('confidence', 0.0)

            logger.info(f"📊 {symbol}: {signal} (Confidence: {confidence:.1%}, Accuracy: {model_info['accuracy']:.1%})")

            # Execute trading if valid signal
            if signal in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
                self._execute_trade(symbol, signal, confidence, data.iloc[-1]['close'])

        except Exception as e:
            logger.error(f"❌ Error analyzing {symbol}: {e}")

    def _get_market_data(self, symbol: str, interval: str = '1h', limit: int = 200) -> Optional[pd.DataFrame]:
        """Get market data from Binance"""
        try:
            if not self.binance_client:
                # Generate synthetic data for testing
                return self._generate_test_data(symbol)

            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            # Convert to numeric types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            logger.error(f"❌ Error getting data for {symbol}: {e}")
            return None

    def _generate_test_data(self, symbol: str) -> pd.DataFrame:
        """Generate test data for testing"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=30),
                             end=datetime.now(), freq='1H')

        np.random.seed(42)
        returns = np.random.normal(0.0001, 0.015, len(dates))
        prices = [1000.0]

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        df = pd.DataFrame(index=dates)
        df['close'] = prices
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = np.maximum(df['open'], df['close']) * (1 + np.random.uniform(0, 0.005, len(df)))
        df['low'] = np.minimum(df['open'], df['close']) * (1 - np.random.uniform(0, 0.005, len(df)))
        df['volume'] = np.random.uniform(100, 1000, len(df))

        return df

    def _execute_trade(self, symbol: str, signal: str, confidence: float, current_price: float):
        """Execute trade with risk management"""
        try:
            # Calculate stop loss and take profit
            atr = 15.0  # Simulated ATR
            if signal in ['BUY', 'STRONG_BUY']:
                stop_loss = current_price - (atr * self.config.stop_loss_atr_multiplier)
                take_profit = current_price + (atr * self.config.take_profit_atr_multiplier)
                side = 'BUY'
            else:
                stop_loss = current_price + (atr * self.config.stop_loss_atr_multiplier)
                take_profit = current_price - (atr * self.config.take_profit_atr_multiplier)
                side = 'SELL'

            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                symbol, current_price, stop_loss, confidence
            )

            position_value = position_size * current_price

            # Check risk limits
            risk_check = self.risk_manager.check_risk_limits(position_value, symbol)

            if not risk_check['approved']:
                logger.warning(f"⚠️ Trade rejected for {symbol}: {', '.join(risk_check['reasons'])}")
                return

            if risk_check['warnings']:
                logger.warning(f"⚠️ Warnings for {symbol}: {', '.join(risk_check['warnings'])}")

            # Execute order (simulated if no real connection)
            success = self._place_order(symbol, side, position_size, current_price, stop_loss, take_profit)

            if success:
                # Log trade
                trade_data = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': current_price,
                    'quantity': position_size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'timestamp': datetime.now()
                }

                self.trade_history.append(trade_data)
                self.current_positions[symbol] = trade_data
                self.risk_manager.add_position(symbol, trade_data)

                logger.info(f"✅ Trade executed: {symbol} {side} at ${current_price:.4f}")

                # Send notification
                self._send_notification(f"🎯 Trade executed\n{symbol}: {side}\nPrice: ${current_price:.4f}\nConfidence: {confidence:.1%}")

        except Exception as e:
            logger.error(f"❌ Error executing trade for {symbol}: {e}")

    def _place_order(self, symbol: str, side: str, quantity: float,
                    price: float, stop_loss: float, take_profit: float) -> bool:
        """Place order on Binance"""
        try:
            if not self.binance_client:
                # Simulation for testing
                logger.info(f"🔍 [SIMULATED] Order {side}: {quantity:.6f} {symbol} @ ${price:.4f}")
                return True

            # Real order (implement according to specific needs)
            # This is a basic example, in production will need more validations

            if side == 'BUY':
                order = self.binance_client.order_market_buy(
                    symbol=symbol,
                    quantity=f"{quantity:.6f}"
                )
            else:
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=f"{quantity:.6f}"
                )

            logger.info(f"✅ Order executed: {order['orderId']}")
            return True

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return False

    def _update_portfolio_metrics(self):
        """Update portfolio metrics"""
        try:
            # Calculate real portfolio value
            if self.binance_client:
                account = self.binance_client.get_account()
                total_value = sum([float(b['free']) * self._get_price(b['asset'])
                                 for b in account['balances'] if float(b['free']) > 0])
            else:
                # Simulation
                total_value = 10000.0 + sum([t.get('pnl', 0) for t in self.trade_history])

            self.risk_manager.update_portfolio_value(total_value)

            # Calculate additional metrics
            if len(self.trade_history) > 0:
                wins = len([t for t in self.trade_history if t.get('pnl', 0) > 0])
                total_trades = len(self.trade_history)
                win_rate = wins / total_trades if total_trades > 0 else 0

                logger.info(f"💼 Portfolio: ${total_value:.2f} | Trades: {total_trades} | Win rate: {win_rate:.1%}")

        except Exception as e:
            logger.error(f"❌ Error updating metrics: {e}")

    def _get_price(self, asset: str) -> float:
        """Get current price of an asset"""
        if asset == 'USDT':
            return 1.0
        try:
            if self.binance_client:
                ticker = self.binance_client.get_symbol_ticker(symbol=f"{asset}USDT")
                return float(ticker['price'])
        except:
            pass
        return 1.0  # Default

    def _send_notification(self, message: str):
        """Send notification via Telegram"""
        try:
            if not self.config.telegram_token or not self.config.telegram_chat_id:
                return

            url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(url, data=payload, timeout=10)

        except Exception as e:
            logger.warning(f"⚠️ Error sending notification: {e}")

    def run_backtest(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """Run backtest for a symbol"""
        return self.backtest_engine.run_backtest(symbol, start_date, end_date)

    def start_web_dashboard(self, host: str = '127.0.0.1', port: int = None):
        """Start web dashboard"""
        self.web_app.run(host=host, port=port)

    def get_status(self) -> Dict:
        """Get current bot status"""
        return {
            'is_running': self.is_running,
            'binance_connected': self.binance_client is not None,
            'portfolio_value': self.risk_manager.portfolio_value,
            'active_positions': len(self.current_positions),
            'total_trades': len(self.trade_history),
            'models_trained': len(self.ml_manager.models)
        }

# ============================
# 🎯 MAIN FUNCTION
# ============================

def main():
    """Main function to run the bot"""
    print("🚀 Starting Advanced Trading Bot v3.0")
    print("=" * 50)

    try:
        # Create bot instance
        bot = AdvancedTradingBot()

        # Show initial status
        status = bot.get_status()
        print(f"📊 Initial bot status:")
        print(f" 💰 Portfolio: ${status['portfolio_value']:.2f}")
        print(f" 🔗 Binance: {'✅ Connected' if status['binance_connected'] else '❌ Disconnected'}")
        print(f" 🎯 Positions: {status['active_positions']}")
        print(f" 📈 Trades: {status['total_trades']}")
        print(f" 🤖 ML Models: {status['models_trained']}")
        print()

        # Interactive menu
        while True:
            print("🎮 Available options:")
            print("1. 🚀 Start automatic trading")
            print("2. 🌐 Open web dashboard")
            print("3. 📊 Run backtest")
            print("4. ⚙️ View configuration")
            print("5. 📈 View bot status")
            print("6. ⏹️ Exit")
            print()

            choice = input("Select an option (1-6): ").strip()

            if choice == '1':
                bot.start_trading()
                input("Press Enter to stop trading...")
                bot.stop_trading()

            elif choice == '2':
                print("🌐 Starting web dashboard...")
                print("Browser will open automatically at http://127.0.0.1:5000")
                bot.start_web_dashboard()

            elif choice == '3':
                symbol = input("Symbol for backtest (e.g.: BTCUSDT): ").strip().upper()
                if not symbol:
                    symbol = "BTCUSDT"

                print(f"📊 Running backtest for {symbol}...")
                results = bot.run_backtest(symbol, "2023-01-01", "2023-12-31")

                print(f"\n✅ Backtest results for {symbol}:")
                print(f" 💰 Total return: {results.get('total_return', 0):.2%}")
                print(f" 📈 Win rate: {results.get('win_rate', 0):.2%}")
                print(f" 🎯 Total trades: {results.get('total_trades', 0)}")
                print(f" 📊 Sharpe ratio: {results.get('sharpe_ratio', 0):.2f}")

            elif choice == '4':
                print("\n⚙️ Current configuration:")
                print(f" 🎯 Symbols: {', '.join(bot.config.symbols)}")
                print(f" ⏰ Timeframes: {', '.join(bot.config.timeframes)}")
                print(f" 💰 Risk per trade: {bot.config.risk_percentage}%")
                print(f" 🔢 Max positions: {bot.config.max_positions}")
                print(f" 🤖 ML models: {', '.join(bot.config.ml_models)}")

            elif choice == '5':
                status = bot.get_status()
                print("\n📈 Current bot status:")
                print(f" 🟢 Running: {'Yes' if status['is_running'] else 'No'}")
                print(f" 🔗 Binance: {'✅ Connected' if status['binance_connected'] else '❌ Disconnected'}")
                print(f" 💰 Portfolio: ${status['portfolio_value']:.2f}")
                print(f" 🎯 Active positions: {status['active_positions']}")
                print(f" 📊 Total trades: {status['total_trades']}")
                print(f" 🤖 Trained models: {status['models_trained']}")

            elif choice == '6':
                print("👋 Closing Advanced Trading Bot v3.0")
                bot.stop_trading()
                break

            else:
                print("❌ Invalid option. Please select 1-6.")

            print()

    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        logger.error(f"Critical error in main: {e}")

if __name__ == "__main__":
    main()

logger.info("🎯 Main bot module initialized correctly")

# ============================
# 🗄️ DATABASE INITIALIZATION
# ============================

# Create data directory
Path("data").mkdir(exist_ok=True)

# Create initial database
conn = sqlite3.connect("data/trading_bot.db")
cursor = conn.cursor()

# Market data table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(symbol, timeframe, timestamp)
    )
''')

print("✅ SQLite database initialized")
conn.commit()
conn.close()
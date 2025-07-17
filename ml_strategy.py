import pandas as pd
import numpy as np
import ta
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MLStrategy:
    """Estrategia de Machine Learning mejorada para trading"""
    
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.last_training = {}
        self.min_data_points = 200
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara características técnicas avanzadas"""
        
        df = df.copy()
        
        # Asegurar que tenemos suficientes datos
        if len(df) < self.min_data_points:
            logger.warning(f"⚠️ Datos insuficientes: {len(df)} < {self.min_data_points}")
            return None
        
        # Precios básicos
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # === INDICADORES TÉCNICOS ===
        
        # Medias móviles
        df['ema_9'] = ta.trend.ema_indicator(df['close'], 9)
        df['ema_21'] = ta.trend.ema_indicator(df['close'], 21)
        df['ema_50'] = ta.trend.ema_indicator(df['close'], 50)
        df['ema_200'] = ta.trend.ema_indicator(df['close'], 200)
        
        # Bandas de Bollinger
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # RSI múltiples timeframes
        df['rsi_14'] = ta.momentum.rsi(df['close'], 14)
        df['rsi_21'] = ta.momentum.rsi(df['close'], 21)
        df['rsi_7'] = ta.momentum.rsi(df['close'], 7)
        
        # MACD
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['macd_signal'] = ta.trend.macd_signal(df['close'])
        df['macd_histogram'] = ta.trend.macd(df['close'])
        
        # Stochastic
        df['stoch_k'] = ta.momentum.stoch(df['high'], df['low'], df['close'])
        df['stoch_d'] = ta.momentum.stoch_signal(df['high'], df['low'], df['close'])
        
        # Williams %R
        df['williams_r'] = ta.momentum.williams_r(df['high'], df['low'], df['close'])
        
        # CCI
        df['cci'] = ta.trend.cci(df['high'], df['low'], df['close'])
        
        # ADX
        df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'])
        
        # === CARACTERÍSTICAS DE PRECIO ===
        
        # Retornos
        df['returns'] = df['close'].pct_change()
        df['returns_2'] = df['close'].pct_change(2)
        df['returns_5'] = df['close'].pct_change(5)
        
        # Volatilidad
        df['volatility'] = df['returns'].rolling(14).std()
        df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(50).mean()
        
        # Rangos
        df['true_range'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        df['price_range'] = (df['high'] - df['low']) / df['close']
        
        # === CARACTERÍSTICAS DE VOLUMEN ===
        
        # Volumen relativo
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # OBV
        df['obv'] = ta.volume.on_balance_volume(df['close'], df['volume'])
        df['obv_ema'] = ta.trend.ema_indicator(df['obv'], 20)
        
        # === CARACTERÍSTICAS DE MOMENTUM ===
        
        # Momentum
        df['momentum'] = df['close'] / df['close'].shift(10)
        df['momentum_short'] = df['close'] / df['close'].shift(5)
        
        # Rate of Change
        df['roc'] = ta.momentum.roc(df['close'])
        
        # === CARACTERÍSTICAS DE SOPORTE/RESISTENCIA ===
        
        # Máximos y mínimos
        df['high_20'] = df['high'].rolling(20).max()
        df['low_20'] = df['low'].rolling(20).min()
        df['price_position'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])
        
        # === CARACTERÍSTICAS DE CRUCE ===
        
        # Cruces de medias
        df['ema_cross_9_21'] = np.where(df['ema_9'] > df['ema_21'], 1, 0)
        df['ema_cross_21_50'] = np.where(df['ema_21'] > df['ema_50'], 1, 0)
        df['price_above_ema200'] = np.where(df['close'] > df['ema_200'], 1, 0)
        
        # === CARACTERÍSTICAS DE PATRÓN ===
        
        # Patrones de velas
        df['doji'] = np.where(abs(df['close'] - df['close'].shift(1)) / df['close'] < 0.001, 1, 0)
        df['hammer'] = np.where(
            (df['close'] > df['close'].shift(1)) & 
            ((df['close'] - df['low']) > 2 * (df['high'] - df['close'])), 1, 0
        )
        
        # === CARACTERÍSTICAS DE TIEMPO ===
        
        # Hora del día (si disponible)
        try:
            df['hour'] = pd.to_datetime(df['timestamp'], unit='ms').dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp'], unit='ms').dt.dayofweek
        except:
            df['hour'] = 0
            df['day_of_week'] = 0
        
        # Limpiar datos
        df = df.dropna()
        
        # Seleccionar características finales
        feature_columns = [
            'ema_9', 'ema_21', 'ema_50', 'ema_200',
            'bb_width', 'bb_position',
            'rsi_14', 'rsi_21', 'rsi_7',
            'macd', 'macd_signal', 'macd_histogram',
            'stoch_k', 'stoch_d', 'williams_r', 'cci', 'adx',
            'returns', 'returns_2', 'returns_5',
            'volatility', 'volatility_ratio', 'true_range', 'price_range',
            'volume_ratio', 'obv', 'obv_ema',
            'momentum', 'momentum_short', 'roc',
            'price_position',
            'ema_cross_9_21', 'ema_cross_21_50', 'price_above_ema200',
            'doji', 'hammer',
            'hour', 'day_of_week'
        ]
        
        # Verificar que todas las columnas existen
        available_features = [col for col in feature_columns if col in df.columns]
        
        logger.info(f"✅ Características preparadas: {len(available_features)} features")
        
        return df[available_features + ['close']]
    
    def create_targets(self, df: pd.DataFrame, prediction_horizon: int = 5) -> pd.DataFrame:
        """Crea targets para el modelo de ML"""
        
        df = df.copy()
        
        # Target 1: Dirección del precio (clasificación)
        df['future_return'] = df['close'].shift(-prediction_horizon) / df['close'] - 1
        df['target_direction'] = np.where(df['future_return'] > 0, 1, 0)
        
        # Target 2: Magnitud del movimiento
        df['target_magnitude'] = np.where(
            abs(df['future_return']) > 0.01, 1, 0  # Movimiento > 1%
        )
        
        # Target 3: Probabilidad de éxito
        rolling_window = 20
        df['success_rate'] = df['target_direction'].rolling(rolling_window).mean()
        
        return df.dropna()
    
    def train_model(self, symbol: str, timeframe: str, df: pd.DataFrame) -> Dict:
        """Entrena el modelo de ML con validación cruzada"""
        
        logger.info(f"🤖 Entrenando modelo para {symbol} [{timeframe}]")
        
        # Preparar datos
        df_features = self.prepare_features(df)
        if df_features is None:
            return None
        
        df_with_targets = self.create_targets(df_features)
        
        # Separar características y targets
        feature_columns = [col for col in df_with_targets.columns 
                          if col not in ['close', 'future_return', 'target_direction', 
                                       'target_magnitude', 'success_rate']]
        
        X = df_with_targets[feature_columns]
        y = df_with_targets['target_direction']
        
        # Dividir en entrenamiento y validación (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Escalar características
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Entrenar múltiples modelos
        models = {
            'rf': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'gb': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        }
        
        best_model = None
        best_score = 0
        best_model_name = None
        
        # Validación cruzada con Time Series Split
        tscv = TimeSeriesSplit(n_splits=5)
        
        for name, model in models.items():
            try:
                # Entrenar modelo
                model.fit(X_train_scaled, y_train)
                
                # Validación cruzada
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv, scoring='accuracy')
                avg_score = cv_scores.mean()
                
                logger.info(f"   {name.upper()}: CV Score = {avg_score:.4f} ± {cv_scores.std():.4f}")
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
                    best_model_name = name
                    
            except Exception as e:
                logger.error(f"❌ Error entrenando {name}: {e}")
        
        if best_model is None:
            logger.error("❌ No se pudo entrenar ningún modelo")
            return None
        
        # Evaluar en validación
        y_pred = best_model.predict(X_val_scaled)
        val_accuracy = (y_pred == y_val).mean()
        
        # Obtener importancia de características
        if hasattr(best_model, 'feature_importances_'):
            feature_importance = dict(zip(feature_columns, best_model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            top_features = []
        
        # Guardar modelo y scaler
        model_key = f"{symbol}_{timeframe}"
        self.models[model_key] = best_model
        self.scalers[model_key] = scaler
        self.feature_importance[model_key] = top_features
        self.last_training[model_key] = datetime.now()
        
        # Guardar modelo en disco
        try:
            joblib.dump(best_model, f'models/{model_key}_model.pkl')
            joblib.dump(scaler, f'models/{model_key}_scaler.pkl')
        except:
            pass  # Crear directorio si no existe
        
        logger.info(f"✅ Modelo {best_model_name.upper()} entrenado:")
        logger.info(f"   📊 CV Score: {best_score:.4f}")
        logger.info(f"   🎯 Val Accuracy: {val_accuracy:.4f}")
        logger.info(f"   🔝 Top features: {[f[0] for f in top_features[:3]]}")
        
        return {
            'model': best_model,
            'scaler': scaler,
            'accuracy': val_accuracy,
            'cv_score': best_score,
            'feature_importance': top_features,
            'model_name': best_model_name
        }
    
    def predict_signal(self, symbol: str, timeframe: str, df: pd.DataFrame) -> Dict:
        """Genera señal de trading usando ML"""
        
        model_key = f"{symbol}_{timeframe}"
        
        # Verificar si el modelo existe
        if model_key not in self.models:
            logger.warning(f"⚠️ Modelo no encontrado para {model_key}")
            return None
        
        # Verificar si necesita reentrenamiento
        if self._needs_retraining(model_key):
            logger.info(f"🔄 Reentrenando modelo para {model_key}")
            self.train_model(symbol, timeframe, df)
        
        # Preparar características
        df_features = self.prepare_features(df)
        if df_features is None:
            return None
        
        # Obtener última fila de características
        latest_features = df_features.iloc[-1:].drop('close', axis=1)
        
        # Escalar características
        scaler = self.scalers[model_key]
        latest_scaled = scaler.transform(latest_features)
        
        # Hacer predicción
        model = self.models[model_key]
        prediction = model.predict(latest_scaled)[0]
        
        # Obtener probabilidades si está disponible
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(latest_scaled)[0]
            confidence = max(probabilities)
        else:
            confidence = 0.5
        
        # Generar señal
        signal = 'BUY' if prediction == 1 else 'SELL'
        
        # Filtrar por confianza mínima
        if confidence < self.config.min_confidence:
            logger.info(f"⚠️ Confianza baja ({confidence:.3f}) para {symbol} [{timeframe}]")
            return None
        
        current_price = df['close'].iloc[-1]
        
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': signal,
            'confidence': confidence,
            'price': current_price,
            'prediction': int(prediction),
            'model_name': model_key,
            'timestamp': datetime.now()
        }
        
        logger.info(f"🎯 Señal ML: {signal} para {symbol} [{timeframe}] - Confianza: {confidence:.3f}")
        
        return result
    
    def _needs_retraining(self, model_key: str) -> bool:
        """Determina si el modelo necesita reentrenamiento"""
        
        if model_key not in self.last_training:
            return True
        
        last_training = self.last_training[model_key]
        hours_since_training = (datetime.now() - last_training).total_seconds() / 3600
        
        return hours_since_training > self.config.model_retrain_hours
    
    def get_model_info(self, symbol: str, timeframe: str) -> Dict:
        """Obtiene información del modelo"""
        
        model_key = f"{symbol}_{timeframe}"
        
        if model_key not in self.models:
            return None
        
        return {
            'model_key': model_key,
            'last_training': self.last_training.get(model_key),
            'feature_importance': self.feature_importance.get(model_key, []),
            'needs_retraining': self._needs_retraining(model_key)
        }
    
    def load_models(self):
        """Carga modelos guardados desde disco"""
        
        try:
            import os
            if not os.path.exists('models'):
                os.makedirs('models')
                return
            
            for filename in os.listdir('models'):
                if filename.endswith('_model.pkl'):
                    model_key = filename.replace('_model.pkl', '')
                    try:
                        self.models[model_key] = joblib.load(f'models/{filename}')
                        self.scalers[model_key] = joblib.load(f'models/{model_key}_scaler.pkl')
                        logger.info(f"✅ Modelo cargado: {model_key}")
                    except Exception as e:
                        logger.error(f"❌ Error cargando {model_key}: {e}")
        except Exception as e:
            logger.error(f"❌ Error cargando modelos: {e}")
    
    def evaluate_model_performance(self, symbol: str, timeframe: str, df: pd.DataFrame) -> Dict:
        """Evalúa el rendimiento del modelo"""
        
        model_key = f"{symbol}_{timeframe}"
        
        if model_key not in self.models:
            return None
        
        # Preparar datos
        df_features = self.prepare_features(df)
        if df_features is None:
            return None
        
        df_with_targets = self.create_targets(df_features)
        
        # Usar últimos 100 puntos para evaluación
        eval_data = df_with_targets.tail(100)
        
        feature_columns = [col for col in eval_data.columns 
                          if col not in ['close', 'future_return', 'target_direction', 
                                       'target_magnitude', 'success_rate']]
        
        X = eval_data[feature_columns]
        y = eval_data['target_direction']
        
        # Escalar y predecir
        scaler = self.scalers[model_key]
        X_scaled = scaler.transform(X)
        
        model = self.models[model_key]
        y_pred = model.predict(X_scaled)
        
        # Calcular métricas
        accuracy = (y_pred == y).mean()
        
        # Calcular precisión por clase
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        precision = precision_score(y, y_pred, average='weighted')
        recall = recall_score(y, y_pred, average='weighted')
        f1 = f1_score(y, y_pred, average='weighted')
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'predictions': len(y_pred),
            'evaluation_period': '100 últimos puntos'
        }
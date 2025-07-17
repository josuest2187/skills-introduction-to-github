# 🤖 Trading Bot Pro

Un bot de trading profesional para criptomonedas con inteligencia artificial, gestión de riesgo avanzada y características de seguridad para inversión real.

## 🚀 Características Principales

### 🧠 Inteligencia Artificial
- **Machine Learning Avanzado**: Modelos Random Forest y Gradient Boosting
- **Feature Engineering**: 40+ indicadores técnicos y características de mercado
- **Validación Cruzada**: TimeSeriesSplit para validación temporal
- **Reentrenamiento Automático**: Modelos actualizados periódicamente

### 🛡️ Gestión de Riesgo
- **Kelly Criterion**: Cálculo óptimo del tamaño de posición
- **Stop Loss Dinámico**: Basado en volatilidad del mercado
- **Límites de Pérdida**: Máximo diario y por posición
- **Correlación**: Prevención de posiciones correlacionadas
- **Parada de Emergencia**: Cierre automático en situaciones críticas

### 🔒 Seguridad
- **Variables de Entorno**: API keys nunca en código
- **Modo Demo**: Pruebas sin riesgo real
- **Validación de Entrada**: Sanitización de todos los inputs
- **Logging Completo**: Auditoría de todas las operaciones

### 📊 Monitoreo y Análisis
- **Base de Datos**: SQLite para persistencia de datos
- **Métricas de Rendimiento**: Sharpe ratio, drawdown, win rate
- **Notificaciones Telegram**: Alertas en tiempo real
- **Interfaz Gráfica**: Control visual del bot

## 🔧 Instalación

### Requisitos
- Python 3.8 o superior
- Cuenta de Binance con API habilitada
- Bot de Telegram (opcional)

### Instalación Automática
```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/trading-bot-pro.git
cd trading-bot-pro

# Ejecutar setup automático
python setup.py
```

### Instalación Manual
```bash
# Instalar dependencias
pip install -r requirements.txt

# Crear directorios
mkdir models logs backups data

# Copiar configuración
cp .env.example .env
```

## ⚙️ Configuración

### 1. Variables de Entorno
Edita el archivo `.env` con tus credenciales:

```bash
# API Keys de Binance
BINANCE_API_KEY=tu_api_key_real
BINANCE_API_SECRET=tu_api_secret_real

# Telegram (opcional)
TELEGRAM_TOKEN=tu_telegram_token
TELEGRAM_CHAT_ID=tu_chat_id

# Base de datos
DATABASE_URL=sqlite:///trading_bot.db
```

### 2. Configuración de Trading
Edita `config.yaml`:

```yaml
# Símbolos a operar
symbols:
  - BTCUSDT
  - ETHUSDT
  - ADAUSDT

# Timeframes de análisis
timeframes:
  - 15m
  - 1h
  - 4h

# Configuración de riesgo
max_daily_loss: 0.05      # 5% pérdida máxima diaria
max_positions: 3          # Máximo 3 posiciones simultáneas
stop_loss_percent: 0.015  # 1.5% stop loss
take_profit_percent: 0.025 # 2.5% take profit

# Machine Learning
min_confidence: 0.65      # Confianza mínima para operar
model_retrain_hours: 24   # Reentrenar cada 24 horas

# Sistema
demo_mode: true          # ¡IMPORTANTE! Cambiar a false para trading real
```

## 🚦 Uso

### Modo Demo (Recomendado para empezar)
```bash
# Asegúrate de que demo_mode: true en config.yaml
python trading_bot_pro.py
```

### Modo Producción
```bash
# Cambiar demo_mode: false en config.yaml
python trading_bot_pro.py
```

### Modo CLI
```bash
python trading_bot_pro.py --cli
```

### Con Scripts
```bash
# Linux/Mac
./start_bot.sh

# Windows
start_bot.bat
```

## 📈 Características Técnicas

### Indicadores Utilizados
- **Medias Móviles**: EMA 9, 21, 50, 200
- **Osciladores**: RSI, Stochastic, Williams %R
- **Momentum**: MACD, CCI, ADX, ROC
- **Volatilidad**: Bandas de Bollinger, ATR
- **Volumen**: OBV, Volume Ratio
- **Patrones**: Doji, Hammer, Cruces

### Estrategia de ML
1. **Preparación de Datos**: Limpieza y normalización
2. **Feature Engineering**: Creación de características técnicas
3. **Entrenamiento**: Modelos ensemble con validación cruzada
4. **Predicción**: Señales con nivel de confianza
5. **Filtrado**: Solo señales con alta confianza

### Gestión de Riesgo
- **Position Sizing**: Kelly Criterion modificado
- **Stop Loss**: Basado en volatilidad
- **Take Profit**: Risk-reward ratio 2:1
- **Correlación**: Máximo 2 posiciones correlacionadas
- **Límites**: Pérdida máxima diaria del 5%

## 📊 Monitoreo

### Métricas Clave
- **PnL Diario**: Ganancias/pérdidas del día
- **Win Rate**: Porcentaje de operaciones exitosas
- **Sharpe Ratio**: Rendimiento ajustado por riesgo
- **Max Drawdown**: Pérdida máxima desde el pico
- **VaR 95%**: Valor en riesgo al 95%

### Logs
- `logs/trading_bot.log`: Log principal
- `logs/error.log`: Solo errores
- Base de datos: Historial completo de operaciones

## 🔧 Mantenimiento

### Backup
```bash
# Backup automático de la base de datos
cp trading_bot.db backups/backup_$(date +%Y%m%d).db

# Exportar datos a CSV
python -c "from database import TradingDatabase; db = TradingDatabase(); db.export_to_csv('positions')"
```

### Limpieza
```bash
# Limpiar datos antiguos (automático)
python -c "from database import TradingDatabase; db = TradingDatabase(); db.cleanup_old_data(90)"
```

### Actualización de Modelos
Los modelos se reentrenan automáticamente cada 24 horas, pero puedes forzar el reentrenamiento:

```python
from ml_strategy import MLStrategy
from config import ConfigManager

config = ConfigManager().config
ml = MLStrategy(config)
ml.train_model('BTCUSDT', '1h', df)
```

## ⚠️ Advertencias Importantes

### 🚨 Riesgos
- **Pérdidas**: El trading de criptomonedas es altamente riesgoso
- **Volatilidad**: Los mercados pueden ser extremadamente volátiles
- **Fallos Técnicos**: Problemas de conectividad pueden afectar operaciones
- **Regulación**: Las regulaciones pueden cambiar

### 🛡️ Recomendaciones de Seguridad
1. **Siempre prueba en modo DEMO primero**
2. **Usa solo capital que puedas permitirte perder**
3. **Monitorea el bot constantemente**
4. **Mantén tus API keys seguras**
5. **Haz backups regulares**
6. **Actualiza el software regularmente**

### 📋 Mejores Prácticas
- Comienza con cantidades pequeñas
- Revisa los logs diariamente
- Ajusta la configuración según el rendimiento
- Mantén un registro manual de operaciones importantes
- Ten un plan de salida de emergencia

## 🆘 Solución de Problemas

### Errores Comunes

#### Error de API Keys
```
❌ API keys de Binance no configuradas
```
**Solución**: Verifica que las variables de entorno estén configuradas correctamente.

#### Error de Conexión
```
❌ Error obteniendo datos de BTCUSDT
```
**Solución**: Verifica la conexión a internet y el estado de la API de Binance.

#### Error de Permisos
```
❌ Error ejecutando trade
```
**Solución**: Verifica que las API keys tengan permisos de trading habilitados.

### Logs de Diagnóstico
```bash
# Ver logs en tiempo real
tail -f logs/trading_bot.log

# Buscar errores específicos
grep "ERROR" logs/trading_bot.log

# Ver estadísticas de la base de datos
sqlite3 trading_bot.db "SELECT COUNT(*) FROM positions;"
```

## 📚 Documentación Adicional

### Estructura del Proyecto
```
trading-bot-pro/
├── trading_bot_pro.py      # Aplicación principal
├── config.py              # Gestión de configuración
├── database.py            # Base de datos
├── risk_manager.py        # Gestión de riesgo
├── ml_strategy.py         # Estrategia de ML
├── requirements.txt       # Dependencias
├── setup.py              # Script de instalación
├── config.yaml           # Configuración principal
├── .env                  # Variables de entorno
├── models/               # Modelos ML guardados
├── logs/                 # Archivos de log
├── backups/              # Backups de la BD
└── data/                 # Datos temporales
```

### API Reference
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## ⚖️ Disclaimer

Este software es solo para fines educativos y de investigación. El trading de criptomonedas involucra riesgos significativos y puede resultar en pérdidas sustanciales. Los usuarios son completamente responsables de sus decisiones de trading y deben consultar con asesores financieros antes de usar este software con capital real.

**NO GARANTIZAMOS GANANCIAS NI ASUMIMOS RESPONSABILIDAD POR PÉRDIDAS.**

---

**¿Necesitas ayuda?** Abre un issue en GitHub o revisa la documentación en los logs.

**¡Happy Trading! 🚀**

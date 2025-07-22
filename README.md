# 🚀 Advanced Trading Bot v2.0

Un bot de trading avanzado para Binance con inteligencia artificial, interfaz gráfica moderna y funciones de seguridad mejoradas.

## ✨ Características Principales

### 🔥 Nuevas Mejoras

- **🏗️ Arquitectura modular**: Código organizado en clases con responsabilidades específicas
- **📊 Machine Learning avanzado**: Modelos RandomForest y GradientBoosting con validación
- **🎯 Análisis multi-timeframe**: Combina señales de 15m, 1h y 4h para mayor precisión
- **🛡️ Gestión de riesgo mejorada**: Límites diarios, balance mínimo, ajuste por confianza
- **🔧 Configuración externa**: Archivo JSON para fácil modificación sin tocar código
- **📱 Interfaz moderna**: GUI con pestañas, logs en tiempo real y estadísticas detalladas
- **🔒 Modo testnet**: Prueba segura antes de usar dinero real
- **📈 Indicadores técnicos ampliados**: 15+ indicadores incluyendo patrones de velas
- **🔄 Cache de modelos**: Reutilización inteligente de modelos entrenados
- **📱 Telegram mejorado**: Mensajes con formato Markdown y reintentos automáticos

### 🎯 Funcionalidades

- ✅ Trading automático 24/7
- ✅ Análisis manual bajo demanda  
- ✅ Múltiples símbolos simultáneos
- ✅ Stop Loss y Take Profit automáticos
- ✅ Historial completo de trades
- ✅ Estadísticas de rendimiento
- ✅ Logs detallados con timestamps
- ✅ Configuración en tiempo real
- ✅ Notificaciones por Telegram

## 🚀 Instalación

### 1. Clonar o descargar los archivos
```bash
# Descargar los archivos del bot:
# - improved_trading_bot.py
# - config.json  
# - requirements.txt
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales
Editar el archivo `config.json`:

```json
{
    "binance": {
        "api_key": "TU_API_KEY_AQUI",
        "api_secret": "TU_API_SECRET_AQUI", 
        "testnet": true
    },
    "telegram": {
        "token": "TU_BOT_TOKEN_AQUI",
        "chat_id": "TU_CHAT_ID_AQUI"
    }
}
```

### 4. Ejecutar el bot
```bash
python improved_trading_bot.py
```

## ⚙️ Configuración Detallada

### 🔑 API de Binance

1. Ve a [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Crea una nueva API Key
3. Habilita "Spot & Margin Trading" 
4. **IMPORTANTE**: Usa primero el testnet para pruebas
5. Para testnet: [Binance Testnet](https://testnet.binance.vision/)

### 📱 Bot de Telegram

1. Habla con [@BotFather](https://t.me/BotFather)
2. Crea un nuevo bot con `/newbot`
3. Copia el token del bot
4. Para obtener tu chat_id: habla con [@userinfobot](https://t.me/userinfobot)

### 🎛️ Parámetros de Trading

```json
"trading": {
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "timeframes": ["15m", "1h", "4h"],
    "limit": 200,
    "risk_percentage": 3,
    "tp_percentage": 2.5, 
    "sl_percentage": 1.5,
    "min_balance": 15,
    "max_trades_per_day": 8
}
```

- **symbols**: Pares de trading a analizar
- **timeframes**: Marcos temporales para análisis
- **limit**: Número de velas históricas
- **risk_percentage**: % del balance por trade
- **tp_percentage**: % de ganancia objetivo
- **sl_percentage**: % de pérdida máxima
- **min_balance**: Balance mínimo requerido
- **max_trades_per_day**: Límite diario de operaciones

### 🤖 Configuración de ML

```json
"ml": {
    "model_type": "RandomForest",
    "n_estimators": 100, 
    "test_size": 0.2,
    "min_accuracy": 0.65
}
```

- **model_type**: "RandomForest" o "GradientBoosting"
- **n_estimators**: Número de árboles en el modelo
- **test_size**: % de datos para validación
- **min_accuracy**: Precisión mínima requerida

## 🎮 Uso de la Interfaz

### 🎯 Pestaña Trading
- **▶️ Iniciar**: Comienza trading automático
- **⏹️ Detener**: Para el bot
- **🔍 Análisis Manual**: Ejecuta análisis único
- **📊 Info de Cuenta**: Balance, trades diarios, win rate
- **📝 Log de Actividad**: Actividad en tiempo real

### ⚙️ Pestaña Configuración  
- Ajustar parámetros de riesgo
- Modificar take profit y stop loss
- Cambiar símbolos de trading
- Guardar configuración

### 📊 Pestaña Estadísticas
- Resumen de trades (ganados/perdidos)
- Win rate histórico
- Historial detallado de operaciones

## 🔒 Seguridad

### ✅ Recomendaciones
- **Siempre usar testnet primero**
- Comenzar con cantidades pequeñas
- Monitorear regularmente el bot
- Configurar límites conservadores
- Mantener API keys seguras

### 🛡️ Características de Seguridad
- Límite máximo de trades diarios
- Balance mínimo requerido
- Validación de modelos ML
- Reintentos con backoff exponencial
- Logs detallados para auditoría

## 📈 Estrategia de Trading

### 🎯 Análisis Multi-timeframe
El bot analiza cada símbolo en múltiples marcos temporales:
- **15m**: Señales de entrada rápidas
- **1h**: Confirmación de tendencia
- **4h**: Contexto de largo plazo

### 🤖 Machine Learning
- Entrena modelos específicos por símbolo
- Usa 15+ indicadores técnicos
- Valida precisión antes de usar
- Cache inteligente de modelos
- Filtros adicionales (RSI, tendencia)

### 💰 Gestión de Capital
- Riesgo ajustado por confianza del modelo
- Stop loss y take profit automáticos
- Límites diarios de operaciones
- Balance mínimo de seguridad

## 📊 Indicadores Utilizados

### 📈 Tendencia
- EMA 9, 21, 50, 200
- ADX (Average Directional Index)
- DM+ y DM- (Directional Movement)

### 📊 Osciladores  
- RSI (Relative Strength Index)
- Stochastic RSI
- CCI (Commodity Channel Index)
- MACD (Moving Average Convergence Divergence)

### 📏 Volatilidad
- Bandas de Bollinger
- Volatilidad histórica

### 📊 Volumen
- OBV (On Balance Volume)
- Accumulation/Distribution Line
- Ratio de volumen

### 🕯️ Patrones de Velas
- Doji
- Hammer
- Engulfing patterns

## 🐛 Solución de Problemas

### ❌ Error de conexión a Binance
- Verificar API key y secret
- Comprobar permisos de la API
- Revisar configuración de testnet

### ❌ No se envían mensajes a Telegram
- Verificar token del bot
- Comprobar chat_id correcto
- Revisar conexión a internet

### ❌ Error de datos insuficientes
- Aumentar el parámetro `limit`
- Verificar que el símbolo existe
- Comprobar conexión a Binance

### ❌ Modelo ML con baja precisión
- Ajustar `min_accuracy` en config
- Cambiar tipo de modelo
- Aumentar datos históricos

## 📝 Logs

El bot genera logs detallados en:
- **Consola**: Actividad en tiempo real
- **trading_bot.log**: Archivo persistente
- **GUI**: Log visual en la interfaz

## 🔄 Actualizaciones

### v2.0 (Actual)
- ✅ Arquitectura completamente refactorizada
- ✅ ML con validación y cache
- ✅ Interfaz gráfica moderna
- ✅ Configuración externa
- ✅ Análisis multi-timeframe
- ✅ Gestión de riesgo avanzada

### v1.0 (Original)
- ✅ Trading básico
- ✅ Indicadores simples
- ✅ Interfaz básica

## ⚠️ Descargo de Responsabilidad

**IMPORTANTE**: Este bot es para fines educativos y experimentales. El trading de criptomonedas conlleva riesgos significativos. Nunca inviertas más de lo que puedes permitirte perder.

- ❌ No garantizamos ganancias
- ❌ Los resultados pasados no garantizan resultados futuros  
- ❌ Usa bajo tu propia responsabilidad
- ✅ Siempre prueba en testnet primero
- ✅ Comienza con cantidades pequeñas

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs en `trading_bot.log`
2. Verifica la configuración en `config.json`
3. Comprueba que todas las dependencias estén instaladas
4. Usa el modo testnet para debugging

## 📄 Licencia

Este proyecto es de código abierto. Úsalo, modifícalo y distribúyelo libremente.

---

**¡Happy Trading! 🚀📈**

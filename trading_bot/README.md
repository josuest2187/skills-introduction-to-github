# Bot de Trading para Binance con Alertas de TradingView

Este proyecto es un bot de trading en Python que utiliza el framework web Flask para escuchar alertas de TradingView a través de webhooks y ejecutar órdenes de mercado en Binance.

## Características

- **Receptor de Webhooks:** Un servidor Flask ligero que escucha las alertas HTTP de TradingView.
- **Integración con Binance:** Se conecta de forma segura a la API de Binance para ejecutar operaciones.
- **Configuración Segura:** Gestiona las claves de API de forma segura utilizando variables de entorno y un archivo `.env`.
- **Lógica Flexible:** Fácil de adaptar para analizar diferentes mensajes de alerta y ejecutar diferentes tipos de órdenes.

## Requisitos

- Python 3.7+
- Una cuenta de Binance con claves de API generadas.
- Una cuenta de TradingView con capacidad para enviar alertas de webhook (requiere un plan de pago de TradingView).

## Guía de Instalación

**1. Clona el repositorio**
```bash
git clone <URL_DEL_REPOSITORIO>
cd trading_bot
```

**2. Crea un Entorno Virtual**
Es una buena práctica usar un entorno virtual para aislar las dependencias del proyecto.
```bash
python -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate
```

**3. Instala las Dependencias**
```bash
pip install -r requirements.txt
```

## Configuración

**1. Configura tus Claves de API**
El bot necesita tus claves de API de Binance para funcionar.

- Crea una copia del archivo de ejemplo `.env.example`:
  ```bash
  cp .env.example .env
  ```
- Abre el archivo `.env` con un editor de texto y reemplaza los valores de ejemplo con tus propias claves de API de Binance.
  ```
  BINANCE_API_KEY="TU_API_KEY_DE_BINANCE"
  BINANCE_API_SECRET="TU_API_SECRET_DE_BINANCE"
  ```
**¡IMPORTANTE!** Nunca compartas este archivo ni subas tus claves a repositorios públicos como GitHub. El archivo `.gitignore` debería incluir `.env` para evitarlo.

**2. Ejecuta el Bot**
Una vez configurado, puedes iniciar el bot con el siguiente comando:
```bash
python app.py
```
Si todo está correcto, verás un mensaje indicando que el servidor Flask se está ejecutando en `http://0.0.0.0:5000`. Esto significa que el bot está listo para recibir alertas.

## Configuración de la Alerta en TradingView

Para que TradingView envíe señales a tu bot, necesitas configurar una alerta con un webhook.

**1. Obtén tu URL de Webhook**
El bot se ejecuta en tu máquina local en el puerto 5000. Para que TradingView (un servicio externo) pueda acceder a él, necesitas exponer ese puerto a internet. Servicios como [ngrok](https://ngrok.com/) son excelentes para esto durante el desarrollo.

- Después de instalar ngrok, ejecuta: `ngrok http 5000`
- ngrok te dará una URL pública (ej. `https://aleatorio.ngrok.io`).
- Tu URL de webhook completa será esa URL más el endpoint `/webhook`. Ejemplo: `https://aleatorio.ngrok.io/webhook`

**2. Crea la Alerta en TradingView**
- Ve a tu gráfico en TradingView y crea una nueva alerta.
- En la configuración de la alerta, ve a la pestaña "Notificaciones".
- Marca la casilla "URL de Webhook" y pega la URL que obtuviste en el paso anterior.
- En el cuadro de "Mensaje", introduce los detalles de la orden en el formato exacto que espera el bot:
  ```
  SYMBOL,SIDE,QUANTITY
  ```
  **Ejemplos de mensajes:**
  - Para comprar 0.01 BTC en el par BTC/USDT: `BTCUSDT,BUY,0.01`
  - Para vender 1.5 ETH en el par ETH/USDT: `ETHUSDT,SELL,1.5`

- Guarda la alerta.

Ahora, cuando la condición de tu alerta se cumpla en TradingView, enviará el mensaje a tu bot, y este ejecutará la orden en Binance. Puedes ver los logs en la terminal donde ejecutas `python app.py`.

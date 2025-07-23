import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from binance_client import BinanceClient

def create_app():
    """
    Application Factory para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    load_dotenv()

    # Cargar la configuración
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        # En un entorno de producción, esto debería ser un error fatal.
        # Para las pruebas, permitiremos que continúe y lo manejaremos en el contexto.
        print("ADVERTENCIA: Las claves de API no están configuradas. El bot no funcionará sin ellas.")
        app.config['BINANCE_CLIENT'] = None
    else:
        try:
            # Adjuntar el cliente de Binance al contexto de la aplicación
            app.config['BINANCE_CLIENT'] = BinanceClient(api_key=api_key, api_secret=api_secret)
        except Exception as e:
            print(f"Error fatal al inicializar el cliente de Binance: {e}")
            app.config['BINANCE_CLIENT'] = None

    # Registrar las rutas/endpoints
    @app.route('/')
    def index():
        return "El servidor del bot de trading está en funcionamiento."

    @app.route('/webhook', methods=['POST'])
    def webhook():
        binance_client = app.config.get('BINANCE_CLIENT')
        if not binance_client:
            return jsonify({"status": "error", "message": "Cliente de Binance no inicializado."}), 503

        print("\n¡Alerta de webhook recibida!")
        try:
            data = request.data.decode('utf-8')
            print(f"Datos recibidos: {data}")

            parts = data.strip().split(',')
            if len(parts) != 3:
                raise ValueError("Formato de datos inválido. Se esperaba 'SYMBOL,SIDE,QUANTITY'.")

            symbol, side, quantity_str = parts
            quantity = float(quantity_str)

            print(f"Intentando ejecutar la orden: {side.upper()} {quantity} {symbol.upper()}")
            order_response = binance_client.create_market_order(symbol.upper(), side.upper(), quantity)

            print("Respuesta de la orden de Binance:", order_response)
            return jsonify({"status": "success", "order_details": order_response}), 200

        except ValueError as e:
            print(f"Error en los datos del webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception as e:
            print(f"Error crítico al procesar el webhook: {e}")
            return jsonify({"status": "error", "message": f"Error interno: {e}"}), 500

    return app

# Este bloque solo se ejecuta cuando se corre el script directamente
if __name__ == '__main__':
    app = create_app()
    if app.config.get('BINANCE_CLIENT'):
        print("Iniciando el servidor Flask del bot...")
        # debug=False es más seguro para un bot que podría manejar dinero real.
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("El servidor no se puede iniciar porque el cliente de Binance no pudo ser inicializado.")

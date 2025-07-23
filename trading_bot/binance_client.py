import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

class BinanceClient:
    """
    Cliente para interactuar con la API de Binance.
    """
    def __init__(self, api_key: str, api_secret: str):
        """
        Inicializa el cliente de Binance.

        Args:
            api_key (str): Tu clave de API de Binance.
            api_secret (str): Tu clave secreta de API de Binance.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        try:
            self.client = Client(self.api_key, self.api_secret)
            # Prueba la conexión a la API
            self.client.ping()
            print("Conexión con Binance establecida exitosamente.")
        except BinanceAPIException as e:
            print(f"Error al conectar con Binance: {e}")
            raise

    def create_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        """
        Crea una orden de mercado.

        Args:
            symbol (str): El par de trading (ej. 'BTCUSDT').
            side (str): El lado de la orden ('BUY' o 'SELL').
            quantity (float): La cantidad a comprar o vender.

        Returns:
            dict: La respuesta de la API de Binance sobre la orden.
        """
        if side.upper() not in ['BUY', 'SELL']:
            raise ValueError("El lado de la orden debe ser 'BUY' o 'SELL'")

        binance_side = Client.SIDE_BUY if side.upper() == 'BUY' else Client.SIDE_SELL

        try:
            print(f"Creando orden de mercado: {side} {quantity} {symbol}...")
            order = self.client.create_order(
                symbol=symbol,
                side=binance_side,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
            print("Orden creada exitosamente.")
            return order
        except BinanceAPIException as e:
            print(f"Error de API al crear la orden: {e}")
            raise
        except BinanceOrderException as e:
            print(f"Error de orden al crear la orden: {e}")
            raise

    def get_account_info(self) -> dict:
        """
        Obtiene la información de la cuenta.

        Returns:
            dict: La información de la cuenta de Binance.
        """
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            print(f"Error al obtener la información de la cuenta: {e}")
            raise

if __name__ == '__main__':
    # Ejemplo de uso (requiere variables de entorno)
    # Para ejecutar esto, necesitarías tener tus claves en el entorno:
    # export BINANCE_API_KEY='tu_api_key'
    # export BINANCE_API_SECRET='tu_api_secret'

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("Error: Las variables de entorno BINANCE_API_KEY y BINANCE_API_SECRET no están configuradas.")
    else:
        print("Claves de API encontradas. Inicializando cliente...")
        binance_client = BinanceClient(api_key=api_key, api_secret=api_secret)

        # 1. Obtener información de la cuenta
        print("\n--- Obteniendo información de la cuenta ---")
        account_info = binance_client.get_account_info()
        if account_info:
            # Imprimir algunos balances de ejemplo
            balances = [b for b in account_info.get('balances', []) if float(b['free']) > 0]
            print("Balances actuales (no cero):")
            for balance in balances:
                print(f"- {balance['asset']}: {balance['free']}")

        # 2. Ejemplo de cómo crear una orden (¡ADVERTENCIA: ESTO EJECUTARÁ UNA ORDEN REAL!)
        # Descomenta las siguientes líneas solo si sabes lo que estás haciendo.
        # print("\n--- Ejemplo de creación de orden ---")
        # try:
        #     # Reemplaza con el símbolo y la cantidad que desees probar
        #     # Se recomienda usar un par de prueba y una cantidad muy pequeña
        #     order_response = binance_client.create_market_order(
        #         symbol='BTCUSDT',
        #         side='BUY',
        #         quantity=0.001
        #     )
        #     print("\nRespuesta de la orden:")
        #     print(order_response)
        # except Exception as e:
        #      print(f"No se pudo ejecutar la orden de ejemplo: {e}")

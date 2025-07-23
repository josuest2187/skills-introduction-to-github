import pytest
from app import create_app

@pytest.fixture
def mock_binance_client(mocker):
    """Un fixture que mockea la clase BinanceClient."""
    mock = mocker.patch('app.BinanceClient')
    # Prevenir que se intente conectar en el __init__
    mock.return_value.ping.return_value = None
    return mock

@pytest.fixture
def app(mock_binance_client):
    """Crea la instancia de la app de Flask para pruebas con el cliente mockeado."""
    # No necesitamos setear variables de entorno porque el cliente ya está mockeado
    # y no se instanciará de verdad.
    app = create_app()
    # Reemplazamos el cliente en la config con nuestro mock para poder hacer asserts.
    app.config['BINANCE_CLIENT'] = mock_binance_client.return_value
    return app

@pytest.fixture
def client(app):
    """Crea un cliente de pruebas para la aplicación Flask."""
    return app.test_client()

def test_webhook_success(client, app):
    """Prueba un webhook exitoso que debería ejecutar una orden."""
    mock_client_instance = app.config['BINANCE_CLIENT']
    mock_client_instance.create_market_order.return_value = {
        "symbol": "BTCUSDT", "orderId": 12345, "status": "FILLED"
    }

    response = client.post('/webhook', data="BTCUSDT,BUY,0.01")

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    mock_client_instance.create_market_order.assert_called_once_with("BTCUSDT", "BUY", 0.01)

def test_webhook_invalid_format(client, app):
    """Prueba un webhook con datos en formato incorrecto."""
    mock_client_instance = app.config['BINANCE_CLIENT']

    response = client.post('/webhook', data="BTCUSDT,SELL")

    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "Formato de datos inválido" in json_data['message']
    mock_client_instance.create_market_order.assert_not_called()

def test_webhook_no_client(client, app):
    """Prueba el caso donde el cliente de Binance no está inicializado."""
    # Forzar que el cliente en la config sea None
    app.config['BINANCE_CLIENT'] = None

    response = client.post('/webhook', data="BTCUSDT,BUY,0.01")

    assert response.status_code == 503 # Service Unavailable
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert "Cliente de Binance no inicializado" in json_data['message']

def test_index_route(client):
    """Prueba la ruta de inicio para asegurar que el servidor está vivo."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"El servidor del bot de trading est" in response.data

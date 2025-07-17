#!/usr/bin/env python3
"""
Setup script para Trading Bot Pro
Instala dependencias y configura el entorno
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando del sistema"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def install_dependencies():
    """Instala las dependencias de Python"""
    print("📦 Instalando dependencias...")
    
    # Actualizar pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Actualizando pip"):
        return False
    
    # Instalar dependencias
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Instalando dependencias"):
        return False
    
    return True

def create_directories():
    """Crea los directorios necesarios"""
    print("📁 Creando directorios...")
    
    directories = [
        'models',
        'logs',
        'backups',
        'data'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/")
    
    return True

def create_config_files():
    """Crea archivos de configuración"""
    print("⚙️ Creando archivos de configuración...")
    
    # Crear config.yaml de ejemplo
    config_content = """# Configuración del Trading Bot Pro
symbols:
  - BTCUSDT
  - ETHUSDT
  - ADAUSDT

timeframes:
  - 15m
  - 1h
  - 4h

# Configuración de trading
base_quantity: 0.001
max_position_size: 0.02
max_daily_loss: 0.05
max_positions: 3

# Configuración de riesgo
stop_loss_percent: 0.015
take_profit_percent: 0.025

# Configuración de ML
model_retrain_hours: 24
min_confidence: 0.65
lookback_periods: 200

# Configuración del sistema
demo_mode: true
log_level: INFO
"""
    
    with open('config.yaml', 'w') as f:
        f.write(config_content)
    
    print("   ✅ config.yaml creado")
    
    # Crear archivo .env de ejemplo
    env_content = """# Variables de entorno para Trading Bot Pro
# IMPORTANTE: Configura estos valores antes de usar el bot

# API Keys de Binance
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_API_SECRET=tu_api_secret_aqui

# Configuración de Telegram
TELEGRAM_TOKEN=tu_telegram_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Base de datos (opcional)
DATABASE_URL=sqlite:///trading_bot.db
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    print("   ✅ .env.example creado")
    
    return True

def create_scripts():
    """Crea scripts de utilidad"""
    print("📝 Creando scripts de utilidad...")
    
    # Script de inicio
    start_script = """#!/bin/bash
# Script de inicio para Trading Bot Pro

echo "🚀 Iniciando Trading Bot Pro..."

# Verificar variables de entorno
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Iniciar bot
python trading_bot_pro.py $@
"""
    
    with open('start_bot.sh', 'w') as f:
        f.write(start_script)
    
    # Hacer ejecutable en Unix
    if platform.system() != 'Windows':
        os.chmod('start_bot.sh', 0o755)
    
    print("   ✅ start_bot.sh creado")
    
    # Script de Windows
    if platform.system() == 'Windows':
        bat_script = """@echo off
echo 🚀 Iniciando Trading Bot Pro...
python trading_bot_pro.py %*
"""
        with open('start_bot.bat', 'w') as f:
            f.write(bat_script)
        print("   ✅ start_bot.bat creado")
    
    return True

def setup_logging():
    """Configura el sistema de logging"""
    print("📋 Configurando logging...")
    
    log_config = """version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
    
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/trading_bot.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 10485760
    backupCount: 5

loggers:
  '':
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
"""
    
    with open('logging.yaml', 'w') as f:
        f.write(log_config)
    
    print("   ✅ logging.yaml creado")
    return True

def print_instructions():
    """Imprime las instrucciones finales"""
    print("\n" + "="*60)
    print("🎉 INSTALACIÓN COMPLETADA")
    print("="*60)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print()
    print("1. 🔑 Configura tus API keys:")
    print("   - Copia .env.example a .env")
    print("   - Edita .env con tus credenciales reales")
    print()
    print("2. ⚙️ Ajusta la configuración:")
    print("   - Edita config.yaml según tus preferencias")
    print("   - Configura símbolos, timeframes y riesgo")
    print()
    print("3. 🧪 Prueba en modo DEMO:")
    print("   - Asegúrate de que demo_mode: true en config.yaml")
    print("   - Ejecuta: python trading_bot_pro.py")
    print()
    print("4. 🚀 Para producción:")
    print("   - Cambia demo_mode: false en config.yaml")
    print("   - Verifica todas las configuraciones")
    print("   - Inicia con capital pequeño")
    print()
    print("📚 COMANDOS ÚTILES:")
    print("   - Interfaz gráfica: python trading_bot_pro.py")
    print("   - Modo CLI: python trading_bot_pro.py --cli")
    print("   - Con script: ./start_bot.sh")
    print()
    print("⚠️ IMPORTANTE:")
    print("   - Siempre prueba en modo DEMO primero")
    print("   - Nunca compartas tus API keys")
    print("   - Monitorea el bot constantemente")
    print("   - Usa solo capital que puedas permitirte perder")
    print()
    print("🆘 SOPORTE:")
    print("   - Revisa los logs en logs/")
    print("   - Verifica la configuración en config.yaml")
    print("   - Consulta la documentación")
    print()
    print("="*60)

def main():
    """Función principal de setup"""
    print("🤖 TRADING BOT PRO - SETUP")
    print("="*40)
    print()
    
    # Verificar Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 o superior requerido")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detectado")
    print(f"✅ Sistema operativo: {platform.system()}")
    print()
    
    # Ejecutar pasos de setup
    steps = [
        ("Instalando dependencias", install_dependencies),
        ("Creando directorios", create_directories),
        ("Creando archivos de configuración", create_config_files),
        ("Creando scripts", create_scripts),
        ("Configurando logging", setup_logging)
    ]
    
    for description, function in steps:
        if not function():
            print(f"❌ Error en: {description}")
            sys.exit(1)
    
    # Mostrar instrucciones finales
    print_instructions()

if __name__ == "__main__":
    main()
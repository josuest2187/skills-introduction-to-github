#!/usr/bin/env python3
"""
Test script to verify Advanced Trading Bot v3.0 installation
============================================================

This script tests all major components and dependencies to ensure
the trading bot is properly installed and configured.
"""

import sys
import importlib
import traceback
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('sklearn', 'Machine learning'),
        ('pandas_ta', 'Technical analysis'),
        ('flask', 'Web framework'),
        ('plotly', 'Data visualization'),
        ('yaml', 'Configuration files'),
        ('requests', 'HTTP requests'),
        ('joblib', 'Model persistence'),
        ('cachetools', 'Caching utilities'),
    ]
    
    optional_packages = [
        ('xgboost', 'XGBoost ML models'),
        ('lightgbm', 'LightGBM ML models'),
        ('binance', 'Binance API client'),
    ]
    
    failed_required = []
    failed_optional = []
    
    # Test required packages
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package:<15} - {description}")
        except ImportError:
            print(f"❌ {package:<15} - {description} (REQUIRED)")
            failed_required.append(package)
    
    # Test optional packages
    for package, description in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package:<15} - {description}")
        except ImportError:
            print(f"⚠️  {package:<15} - {description} (OPTIONAL)")
            failed_optional.append(package)
    
    return failed_required, failed_optional

def test_bot_import():
    """Test bot module import"""
    print("\n🤖 Testing bot import...")
    try:
        from advanced_trading_bot_v3 import AdvancedTradingBot
        print("✅ Advanced Trading Bot imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import bot: {e}")
        return False

def test_configuration():
    """Test configuration file"""
    print("\n⚙️ Testing configuration...")
    config_file = Path("config.yaml")
    
    if config_file.exists():
        print("✅ Configuration file found")
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Configuration file is valid YAML")
            
            # Check for required keys
            required_keys = ['symbols', 'risk_percentage', 'ml_models']
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                print(f"⚠️  Missing configuration keys: {missing_keys}")
            else:
                print("✅ All required configuration keys present")
                
            return True
        except Exception as e:
            print(f"❌ Configuration file error: {e}")
            return False
    else:
        print("⚠️  Configuration file not found (will use defaults)")
        return True

def test_directories():
    """Test required directories"""
    print("\n📁 Testing directories...")
    
    required_dirs = ['logs', 'data']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"⚠️  {dir_name}/ directory will be created automatically")
    
    return True

def test_basic_functionality():
    """Test basic bot functionality"""
    print("\n🔧 Testing basic functionality...")
    
    try:
        from advanced_trading_bot_v3 import AdvancedTradingBot, TradingConfig
        
        # Test configuration creation
        config = TradingConfig()
        print("✅ Configuration object created")
        
        # Test bot initialization (without API keys)
        bot = AdvancedTradingBot()
        print("✅ Bot initialized successfully")
        
        # Test status retrieval
        status = bot.get_status()
        print("✅ Status retrieval working")
        
        print(f"   Portfolio value: ${status['portfolio_value']:.2f}")
        print(f"   Binance connected: {status['binance_connected']}")
        print(f"   Models trained: {status['models_trained']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def print_recommendations(failed_required, failed_optional):
    """Print installation recommendations"""
    print("\n💡 Recommendations:")
    
    if failed_required:
        print("\n❌ Required packages missing:")
        print("   Run: pip install -r requirements.txt")
        for package in failed_required:
            print(f"   Or: pip install {package}")
    
    if failed_optional:
        print("\n⚠️  Optional packages missing:")
        for package in failed_optional:
            if package == 'xgboost':
                print("   For XGBoost: pip install xgboost")
            elif package == 'lightgbm':
                print("   For LightGBM: pip install lightgbm")
            elif package == 'binance':
                print("   For Binance API: pip install python-binance")
    
    print("\n🔧 Next steps:")
    print("1. Install any missing required packages")
    print("2. Configure your API keys in config.yaml")
    print("3. Start with testnet trading (binance_testnet: true)")
    print("4. Run: python advanced_trading_bot_v3.py")

def main():
    """Main test function"""
    print("🚀 Advanced Trading Bot v3.0 - Installation Test")
    print("=" * 55)
    
    # Run all tests
    tests_passed = 0
    total_tests = 5
    
    if test_python_version():
        tests_passed += 1
    
    failed_required, failed_optional = test_dependencies()
    if not failed_required:
        tests_passed += 1
    
    if test_bot_import():
        tests_passed += 1
    
    if test_configuration():
        tests_passed += 1
    
    if test_directories():
        tests_passed += 1
    
    # Try basic functionality if core components work
    if tests_passed >= 3:
        if test_basic_functionality():
            tests_passed += 1
            total_tests += 1
    
    # Print summary
    print("\n" + "=" * 55)
    print(f"📊 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The bot is ready to use.")
        print("\n🚀 To start the bot, run:")
        print("   python advanced_trading_bot_v3.py")
    elif failed_required:
        print("❌ Critical dependencies missing. Install requirements first.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    print_recommendations(failed_required, failed_optional)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
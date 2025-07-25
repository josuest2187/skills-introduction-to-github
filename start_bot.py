#!/usr/bin/env python3
"""
🚀 Advanced Trading Bot v3.0 - Quick Start Script
=================================================

Quick launcher for the Advanced Trading Bot with different modes.
"""

import sys
import argparse
from pathlib import Path

def check_installation():
    """Quick installation check"""
    try:
        from advanced_trading_bot_v3 import AdvancedTradingBot
        return True
    except ImportError as e:
        print(f"❌ Installation error: {e}")
        print("\n💡 Please run the installation test first:")
        print("   python test_installation.py")
        return False

def start_interactive_mode():
    """Start interactive mode with menu"""
    print("🚀 Starting Advanced Trading Bot v3.0 - Interactive Mode")
    print("=" * 60)
    
    if not check_installation():
        return False
    
    from advanced_trading_bot_v3 import main
    main()
    return True

def start_trading_mode(config_path="config.yaml"):
    """Start automatic trading mode"""
    print("🚀 Starting Advanced Trading Bot v3.0 - Trading Mode")
    print("=" * 60)
    
    if not check_installation():
        return False
    
    from advanced_trading_bot_v3 import AdvancedTradingBot
    
    try:
        bot = AdvancedTradingBot(config_path)
        
        # Show initial status
        status = bot.get_status()
        print(f"💰 Portfolio: ${status['portfolio_value']:.2f}")
        print(f"🔗 Binance: {'✅ Connected' if status['binance_connected'] else '❌ Disconnected'}")
        print(f"🎯 Symbols: {', '.join(bot.config.symbols)}")
        print(f"⚠️  Testnet: {bot.config.binance_testnet}")
        print()
        
        # Confirm before starting
        if not bot.config.binance_testnet:
            confirm = input("⚠️  LIVE TRADING MODE! Are you sure? (type 'YES' to confirm): ")
            if confirm != 'YES':
                print("❌ Trading cancelled.")
                return False
        
        print("🚀 Starting automated trading...")
        bot.start_trading()
        
        try:
            input("Press Enter to stop trading...")
        except KeyboardInterrupt:
            pass
        
        bot.stop_trading()
        print("⏹️ Trading stopped.")
        return True
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        return False

def start_dashboard_mode(config_path="config.yaml", host="127.0.0.1", port=5000):
    """Start web dashboard mode"""
    print("🌐 Starting Advanced Trading Bot v3.0 - Dashboard Mode")
    print("=" * 60)
    
    if not check_installation():
        return False
    
    from advanced_trading_bot_v3 import AdvancedTradingBot
    
    try:
        bot = AdvancedTradingBot(config_path)
        print(f"🌐 Starting web dashboard at http://{host}:{port}")
        print("💡 Browser will open automatically")
        print("🛑 Press Ctrl+C to stop the dashboard")
        
        bot.start_web_dashboard(host=host, port=port)
        return True
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False

def start_backtest_mode(config_path="config.yaml", symbol="BTCUSDT", 
                       start_date="2023-01-01", end_date="2023-12-31"):
    """Start backtesting mode"""
    print("📊 Starting Advanced Trading Bot v3.0 - Backtest Mode")
    print("=" * 60)
    
    if not check_installation():
        return False
    
    from advanced_trading_bot_v3 import AdvancedTradingBot
    
    try:
        bot = AdvancedTradingBot(config_path)
        
        print(f"📊 Running backtest for {symbol}")
        print(f"📅 Period: {start_date} to {end_date}")
        print("⏳ This may take a few minutes...")
        
        results = bot.run_backtest(symbol, start_date, end_date)
        
        print("\n" + "=" * 60)
        print(f"📈 Backtest Results for {symbol}")
        print("=" * 60)
        print(f"💰 Total Return:    {results.get('total_return', 0):.2%}")
        print(f"📊 Sharpe Ratio:    {results.get('sharpe_ratio', 0):.2f}")
        print(f"📉 Max Drawdown:    {results.get('max_drawdown', 0):.2%}")
        print(f"🎯 Win Rate:        {results.get('win_rate', 0):.2%}")
        print(f"🔢 Total Trades:    {results.get('total_trades', 0)}")
        print(f"💵 Initial Capital: ${results.get('initial_capital', 0):,.2f}")
        print(f"💰 Final Capital:   ${results.get('final_capital', 0):,.2f}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Advanced Trading Bot v3.0 - Quick Start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_bot.py                          # Interactive mode
  python start_bot.py --mode trading           # Start automated trading
  python start_bot.py --mode dashboard         # Start web dashboard
  python start_bot.py --mode backtest          # Run backtest
  python start_bot.py --mode backtest --symbol ETHUSDT  # Backtest ETHUSDT
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['interactive', 'trading', 'dashboard', 'backtest'],
        default='interactive',
        help='Bot operation mode (default: interactive)'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Dashboard host (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Dashboard port (default: 5000)'
    )
    
    parser.add_argument(
        '--symbol',
        default='BTCUSDT',
        help='Symbol for backtesting (default: BTCUSDT)'
    )
    
    parser.add_argument(
        '--start-date',
        default='2023-01-01',
        help='Backtest start date (default: 2023-01-01)'
    )
    
    parser.add_argument(
        '--end-date',
        default='2023-12-31',
        help='Backtest end date (default: 2023-12-31)'
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists() and args.config != 'config.yaml':
        print(f"❌ Configuration file not found: {args.config}")
        return False
    
    # Route to appropriate mode
    if args.mode == 'interactive':
        return start_interactive_mode()
    
    elif args.mode == 'trading':
        return start_trading_mode(args.config)
    
    elif args.mode == 'dashboard':
        return start_dashboard_mode(args.config, args.host, args.port)
    
    elif args.mode == 'backtest':
        return start_backtest_mode(
            args.config, args.symbol, args.start_date, args.end_date
        )
    
    else:
        print(f"❌ Unknown mode: {args.mode}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
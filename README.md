# 🚀 Advanced Trading Bot v3.0

A professional-grade cryptocurrency trading bot with advanced Machine Learning, comprehensive backtesting, real-time web dashboard, and sophisticated risk management.

## ✨ Features

### 🤖 Advanced Machine Learning
- **Ensemble Models**: Random Forest, XGBoost, LightGBM with voting classifier
- **Feature Engineering**: 100+ technical indicators and market structure features
- **Cross-Validation**: Time series split for robust model validation
- **Auto-Retraining**: Periodic model updates to adapt to market conditions

### 📊 Professional Backtesting
- **Comprehensive Metrics**: Sharpe ratio, Sortino ratio, Maximum Drawdown, VaR
- **Realistic Simulation**: Commission, slippage, and market impact modeling
- **Performance Analytics**: Win rate, profit factor, trade analysis

### 💰 Advanced Risk Management
- **Position Sizing**: Fixed, volatility-adjusted, and Kelly criterion methods
- **Dynamic Stop Loss**: ATR-based stop loss and take profit levels
- **Portfolio Limits**: Maximum positions, drawdown limits, correlation checks
- **Real-time Monitoring**: Continuous risk assessment and position management

### 🌐 Interactive Web Dashboard
- **Real-time Portfolio**: Live portfolio value, P&L, and position tracking
- **Trading Signals**: ML-generated signals with confidence levels
- **Performance Charts**: Interactive charts with Plotly
- **Backtesting Interface**: Run backtests directly from the web interface

### 🔔 Notifications & Alerts
- **Telegram Integration**: Real-time trade notifications
- **Discord Webhooks**: Server notifications for trading events
- **Email Alerts**: SMTP-based email notifications

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd advanced-trading-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the bot**
```bash
# Edit config.yaml with your settings
cp config.yaml.template config.yaml
nano config.yaml
```

4. **Add your API keys**
```yaml
# In config.yaml
binance_api_key: "your_binance_api_key"
binance_api_secret: "your_binance_api_secret"
binance_testnet: true  # Start with testnet!
```

5. **Run the bot**
```bash
python advanced_trading_bot_v3.py
```

## 🚀 Quick Start

### 1. Test Mode (Recommended)
```bash
# Run with simulated data (no real trading)
python advanced_trading_bot_v3.py
# Select option 1 to start trading simulation
```

### 2. Web Dashboard
```bash
python advanced_trading_bot_v3.py
# Select option 2 to open web dashboard
# Navigate to http://localhost:5000
```

### 3. Backtesting
```bash
python advanced_trading_bot_v3.py
# Select option 3 to run backtests
# Enter symbol (e.g., BTCUSDT) when prompted
```

## ⚙️ Configuration

### Trading Parameters
```yaml
symbols:
  - "BTCUSDT"
  - "ETHUSDT"
  # Add more trading pairs

risk_percentage: 2.0  # Risk 2% per trade
max_positions: 5      # Maximum 5 open positions
```

### Machine Learning Settings
```yaml
ml_models:
  - "randomforest"
  - "xgboost"
  - "lightgbm"

min_accuracy: 0.65    # Minimum 65% accuracy
training_window: 1000 # Use 1000 data points for training
```

### Risk Management
```yaml
stop_loss_atr_multiplier: 2.0    # Stop loss at 2x ATR
take_profit_atr_multiplier: 3.0  # Take profit at 3x ATR
max_drawdown_percent: 15.0       # Max 15% drawdown
```

## 📈 Usage Examples

### Automated Trading
```python
from advanced_trading_bot_v3 import AdvancedTradingBot

# Create bot instance
bot = AdvancedTradingBot("config.yaml")

# Start automated trading
bot.start_trading()

# Check status
status = bot.get_status()
print(f"Portfolio: ${status['portfolio_value']:.2f}")
print(f"Active positions: {status['active_positions']}")
```

### Custom Backtesting
```python
# Run backtest for specific symbol and period
results = bot.run_backtest(
    symbol="BTCUSDT",
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Win Rate: {results['win_rate']:.2%}")
```

### Web Dashboard API
```python
# Access portfolio data via API
import requests

response = requests.get("http://localhost:5000/api/portfolio")
portfolio = response.json()

print(f"Total Value: ${portfolio['total_value']}")
print(f"Daily P&L: ${portfolio['daily_pnl']}")
```

## 🔧 Advanced Features

### Custom Indicators
```python
class CustomFeatureEngineer(FeatureEngineer):
    def add_custom_indicators(self, df):
        # Add your custom technical indicators
        df['custom_rsi'] = custom_rsi_calculation(df['close'])
        return df
```

### Custom Risk Management
```python
class CustomRiskManager(RiskManager):
    def custom_position_sizing(self, symbol, confidence):
        # Implement your position sizing logic
        return calculated_size
```

### Notification Customization
```python
def custom_notification(self, message, level="INFO"):
    if level == "CRITICAL":
        # Send to multiple channels
        self.send_telegram(message)
        self.send_discord(message)
        self.send_email(message)
```

## 📊 Performance Metrics

The bot tracks comprehensive performance metrics:

- **Return Metrics**: Total return, annualized return, monthly returns
- **Risk Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown, VaR
- **Trade Metrics**: Win rate, profit factor, average win/loss
- **Efficiency Metrics**: Calmar ratio, Sterling ratio, recovery factor

## 🔒 Security & Risk Warnings

### ⚠️ Important Disclaimers

1. **Start with Testnet**: Always test with Binance testnet before live trading
2. **Risk Management**: Never risk more than you can afford to lose
3. **API Security**: Keep your API keys secure and use IP restrictions
4. **Backtesting Limitations**: Past performance doesn't guarantee future results
5. **Market Risks**: Cryptocurrency markets are highly volatile and risky

### Security Best Practices

```yaml
# Recommended API permissions (Binance)
# ✅ Enable: Spot & Margin Trading
# ❌ Disable: Futures Trading (unless needed)
# ❌ Disable: Withdrawals
# ✅ Enable: IP Restriction
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt

# For TA-Lib issues on Windows:
pip install TA-Lib‑0.4.25‑cp39‑cp39‑win_amd64.whl
```

2. **API Connection Issues**
```python
# Check API credentials
# Verify IP restrictions
# Ensure sufficient permissions
```

3. **Memory Issues**
```python
# Reduce training window size
training_window: 500  # Instead of 1000

# Limit number of symbols
symbols: ["BTCUSDT"]  # Start with one pair
```

## 📝 Logging

The bot provides comprehensive logging:

```
logs/
├── advancedtradingbot.log     # Main application log
├── trades.log                 # Trade execution log
├── errors.log                 # Error log
└── performance.log            # Performance metrics log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

This project is for educational purposes. Use at your own risk.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue with detailed information

---

**⚠️ Disclaimer**: This software is for educational purposes only. Trading cryptocurrencies involves substantial risk and may result in significant financial losses. Always do your own research and consider consulting with financial advisors before making investment decisions.

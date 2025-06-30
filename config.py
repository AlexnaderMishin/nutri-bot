import os

# Telegram Bot
BOT_TOKEN = "7144225641:AAEiEO5S0ofPreoftsuFJKiNToSWhEqNa-I"

# GigaChat API
GIGACHAT_AUTH_KEY = "NmU5ZjRjYTgtMTQ1OC00NTE5LTk0N2EtODBiZjFiZjE3ZTcyOjVmMzNiMGQ3LWZlMzQtNDc5MC05NTgxLTQ0OTIwOWJiODRiOA=="

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nutri.db")  # Fallback to SQLite
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7144225641:AAEiEO5S0ofPreoftsuFJKiNToSWhEqNa-I")
    GIGACHAT_AUTH_KEY = os.getenv("NmU5ZjRjYTgtMTQ1OC00NTE5LTk0N2EtODBiZjFiZjE3ZTcyOjVmMzNiMGQ3LWZlMzQtNDc5MC05NTgxLTQ0OTIwOWJiODRiOA==")
    
config = Config()
# import os
# BOT_TOKEN = "7144225641:AAEiEO5S0ofPreoftsuFJKiNToSWhEqNa-I"
# GIGACHAT_TOKEN = ""
# GIGACHAT_AUTH_KEY = "NmU5ZjRjYTgtMTQ1OC00NTE5LTk0N2EtODBiZjFiZjE3ZTcyOjVmMzNiMGQ3LWZlMzQtNDc5MC05NTgxLTQ0OTIwOWJiODRiOA=="

# DATABASE_URL = os.getenv("DATABASE_URL")
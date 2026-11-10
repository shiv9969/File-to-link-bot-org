# (c) adarsh-goel (c) @biisal
import os
from os import getenv, environ
from dotenv import load_dotenv



load_dotenv()


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


bot_name = "BoB Link Generator"
bisal_channel = "https://telegram.me/BoB_Files1"
bisal_grp = "https://t.me/REQUESTING_MOVIES_SERIES_GROUPS"

class Var(object):
    MULTI_CLIENT = False
    API_ID = int(getenv('API_ID', '9301087'))
    API_HASH = str(getenv('API_HASH', ''))
    BOT_TOKEN = str(getenv('BOT_TOKEN', ''))
    name = str(getenv('name', 'FToLStreamBot'))
    SLEEP_THRESHOLD = int(getenv('SLEEP_THRESHOLD', '60'))
    WORKERS = int(getenv('WORKERS', '4'))
    BIN_CHANNEL = int(getenv('BIN_CHANNEL', '-1001916812956'))
    NEW_USER_LOG = int(getenv('NEW_USER_LOG', '-1001844691460'))
    PORT = int(getenv('PORT', '8080'))
    BIND_ADRESS = str(getenv('WEB_SERVER_BIND_ADDRESS', '0.0.0.0'))
    PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
    OWNER_ID = set(int(x) for x in os.environ.get("OWNER_ID", "1525203313").split())  
    NO_PORT = _as_bool(getenv('NO_PORT', 'false'))
    APP_NAME = str(getenv("APP_NAME", "")).strip()
    OWNER_USERNAME = str(getenv("OWNER_USERNAME", "Assaulter_Shiv"))
    ON_HEROKU = "DYNO" in environ

    if ON_HEROKU:
        FQDN = str(getenv("FQDN", "")).strip() or (
            f"{APP_NAME}.herokuapp.com" if APP_NAME else ""
        )
    else:
        FQDN = str(getenv("FQDN", "")).strip() or f"{BIND_ADRESS}:{PORT}"
    HAS_SSL = _as_bool(getenv('HAS_SSL', 'true'), default=True)
    if HAS_SSL:
        URL = "https://{}/".format(FQDN)
    else:
        URL = "http://{}/".format(FQDN)
    DATABASE_URL = str(getenv('DATABASE_URL', ''))
    UPDATES_CHANNEL = str(getenv('UPDATES_CHANNEL', 'BoB_Files1')) 
    BANNED_CHANNELS = list(set(int(x) for x in str(getenv("BANNED_CHANNELS", "")).split() if x.lstrip("-").isdigit()))   
    BAN_CHNL = list(set(int(x) for x in str(getenv("BAN_CHNL", "")).split() if x.lstrip("-").isdigit()))   
    

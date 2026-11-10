# (c) adarsh-goel (c) @biisal
import os
from os import getenv, environ
from dotenv import load_dotenv



load_dotenv()
bot_name = "BoB Link Generator"
bisal_channel = "https://telegram.me/BoB_Files1"
bisal_grp = "https://t.me/REQUESTING_MOVIES_SERIES_GROUPS"

class Var(object):
    MULTI_CLIENT = False
    API_ID = int(getenv('API_ID', '9301087'))
    API_HASH = str(getenv('API_HASH', 'cbabdb3f23de6326352ef3ac26338d9c'))
    BOT_TOKEN = str(getenv('BOT_TOKEN' , '7368488558:AAFJZYQoRsnaf4v0UR2NlTRiIj6GnnbwnvY'))
    name = str(getenv('name', 'FToLStreamBot'))
    SLEEP_THRESHOLD = int(getenv('SLEEP_THRESHOLD', '60'))
    WORKERS = int(getenv('WORKERS', '4'))
    BIN_CHANNEL = int(getenv('BIN_CHANNEL', '-1001916812956'))
    NEW_USER_LOG = int(getenv('NEW_USER_LOG', '-1001844691460'))
    PORT = int(getenv('PORT', '8080'))
    BIND_ADRESS = str(getenv('WEB_SERVER_BIND_ADDRESS', '0.0.0.0'))
    PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
    OWNER_ID = set(int(x) for x in os.environ.get("OWNER_ID", "1525203313").split())  
    NO_PORT = bool(getenv('NO_PORT', False))
    APP_NAME = None
    OWNER_USERNAME = str(getenv('OWNER_USERNAME', 'Assaulter_Shiv'))
    if 'DYNO' in environ:
        ON_HEROKU = True
        APP_NAME = str(getenv('APP_NAME')) #dont need to fill anything here
    
    else:
        ON_HEROKU = False
    FQDN = str(getenv('FQDN', 'BIND_ADRESS:PORT')) if not ON_HEROKU or getenv('FQDN', '') else APP_NAME+'.herokuapp.com'
    HAS_SSL=bool(getenv('HAS_SSL',True))
    if HAS_SSL:
        URL = "https://{}/".format(FQDN)
    else:
        URL = "http://{}/".format(FQDN)
    DATABASE_URL = str(getenv('DATABASE_URL', 'mongodb+srv://Kissu:Kissimunda.888@cluster0.f8ssexm.mongodb.net/?retryWrites=true&w=majority'))
    UPDATES_CHANNEL = str(getenv('UPDATES_CHANNEL', 'BoB_Files1')) 
    BANNED_CHANNELS = list(set(int(x) for x in str(getenv("BANNED_CHANNELS", "")).split()))   
    BAN_CHNL = list(set(int(x) for x in str(getenv("BAN_CHNL", "")).split()))   
    

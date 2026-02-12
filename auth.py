from itsdangerous import URLSafeSerializer
from config import settings

ser = URLSafeSerializer(settings.SECRET)

def make_session(username):
    return ser.dumps(username)

def read_session(token):
    try:
        return ser.loads(token)
    except:
        return None

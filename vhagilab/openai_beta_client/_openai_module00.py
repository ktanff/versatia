from ..cache import cache
@cache()
def safe_provider( GATEWAY, CONNECTION_PROTOCOL="https" ):
    import requests
    OPENAI_BASE = "api.openai.com"
    if GATEWAY[-14:] == OPENAI_BASE: return "Bad gateway!"
    if CONNECTION_PROTOCOL[-4:] == "http":
        OPENAI_BASE = GATEWAY
        CONNECTION_PROTOCOL = CONNECTION_PROTOCOL[-4:]+CONNECTION_PROTOCOL[:-4]
    response = requests.get('https://api.ipify.org')
    public_ip = response.text
    #print(f'Public IP Address: {public_ip}')
    iploctn = requests.get(f'https://api.iplocation.net/?ip={public_ip}').json()
    print(iploctn)
    #print(iploctn['country_name'], 'Not safe!' if iploctn['country_code2']=='IR' else 'safe country')
    if iploctn['country_code2']=='IR': # quit()
        OPENAI_BASE = GATEWAY
        CONNECTION_PROTOCOL == "https"
    OPENAI_BASE_URL = CONNECTION_PROTOCOL + "://" + OPENAI_BASE
    #print(OPENAI_BASE_URL)
    return OPENAI_BASE_URL, iploctn['ip_number']

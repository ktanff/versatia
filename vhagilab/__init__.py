from . import openai_beta_client
from .openai_beta_client import *
from . import gradio_utils
# "from . import sess_utils.*" implicitly imported into gradio_utils

from .token import *
from .lambdas import *
from .gentrait import *
from .cache import *
from .fallback import *
from .thread_registry import *
from .calendars_conversion import *

from . import user_credential
from . import user_registration
from . import notif_utils
from . import vhfront_msg

from atexit import register as _atexit_register

with open('app_schema.json',encoding='utf-8') as _app_schema_file:
    from json import load
    app_schema = load(_app_schema_file)
    with open(app_schema['PERSONA']+'.json',encoding='utf-8') as persona_file:
        persona = load(persona_file)
    assert app_schema['ORGANIZATION']==persona['ORGANIZATION'], "Organizations on app schema and persona not matched."
    assert app_schema['CASE']==persona['CASE'], "Cases on app schema and persona not matched."
    openai_beta_client.set_config(app_schema['OPENAI_CONFIG'])
    gradio_utils.set_default_tagline(**app_schema)
    
    set_cache_era(app_schema['APP_SESSION_ERA'])
    _atexit_register(cache_dump)
    user_credential.load(app_schema)
    _atexit_register(user_credential.save,app_schema)
    notif_utils.setup(app_schema['NOTIF_CONFIG'])
    vhfront_msg.load(app_schema['FRONT_MSGS'])

user_registration.load()
_atexit_register(user_registration.save)
_atexit_register(dump_thread_registry)

from vhagilab import *
from vhagilab import gradio_utils as gu

if __name__ == '__main__':
    if user_credential.cli():
        quit()
    # Create the useful aSessionPlatform!
    import setupASessionPlatform
    # Then, aSessionPlatform() returns a basic cookie-based session platform that
    # is accessible everywhere, simply by
    # `from vhagilab.aSessionPlatform import aSessionPlatform`
    import admin
    admin.admin.queue(max_size=1,default_concurrency_limit=4)
    gu.mount_module_blocks(admin,path="/admin",privileged_users='@admin')
    import registration
    registration.register.queue(max_size=40,default_concurrency_limit=8)
    gu.mount_module_blocks(registration,path="/register")
    import signin
    signin.signin.queue(max_size=20,default_concurrency_limit=4)
    gu.mount_module_blocks(signin,path="/signin")
    import special_guest
    special_guest.special_guest.queue(max_size=20,default_concurrency_limit=8)
    gu.mount_module_blocks(special_guest,path="/special_guest")
    import guest
    guest.guest.queue(max_size=20,default_concurrency_limit=8)
    gu.mount_module_blocks(guest,path="/guest")
    import pwchange
    pwchange.pwchange.queue(max_size=40,default_concurrency_limit=8)
    gu.mount_module_blocks(pwchange,path="/pwchange")
    import app
    app.app.queue(max_size=20,default_concurrency_limit=4)
    gu.mount_module_blocks(app,path="")
    gu.run(
        root_path = app_schema.get('ROOTPATH',''),
        host = app_schema.get('HOST','127.0.0.1'),
        port = app_schema.get('GRADIO_PORT',7860),
        ssl_certfile=app_schema.get('SSL_CERTFILE'),
        ssl_keyfile=app_schema.get('SSL_KEYFILE')
   )
### The path to static files
# from importlib import resources
# print(resources.files("gradio").joinpath("templates/frontend/static"))

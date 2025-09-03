
## How to launch
- <code>python the_app.py</code>
- Try as guest, without password, or use test:test.

## Configurations
- **app_schema.json** -- The application settings.
- **openai_client_config_*.json** -- Settings for openai client.
- **credentials.json** -- Just a username:passwrod dictionary.

## SSL Config
- ssl_keyfile.pem could be simply a symlink to "/etc/letsencrypt/live/yoursite.yourdomain.com/fullchain.pem"
- ssl_certfile.pem could be simply a symlink to "/etc/letsencrypt/live/yoursite.yourdomain.com/privkey.pem"

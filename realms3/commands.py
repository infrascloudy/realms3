import os
import click

from realms3 import config, create_app
from realms3.lib.util import random_string, in_virtualenv, green, yellow, red

config = config.conf
app = create_app()

def get_user():
    for name in ('SUDO_USER', 'LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            return user

def get_pid():
    try:
        with open(config.PIDFILE) as f:
            return f.read().strip()
    except IOError:
        return None

def is_running(pid):
    if not pid:
        return False

    pid = int(pid)

    try:
        os.kill(pid, 0)
    except OSError:
        return False

    return True


def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True


def prompt_and_invoke(ctx, fn):
    kw = {}

    for p in fn.params:
        v = click.prompt(p.prompt, p.default, p.hide_input,
                         p.confirmation_prompt, p.type)
        kw[p.name] = v

    ctx.invoke(fn, **kw)


@app.cli.command()
@click.option('--site-title',
              default=config.SITE_TITLE,
              prompt='Enter site title.')
@click.option('--base_url',
              default=config.BASE_URL,
              prompt='Enter base URL.')
@click.option('--port',
              default=config.PORT,
              prompt='Enter port number.')
@click.option('--secret-key',
              default=config.SECRET_KEY if config.SECRET_KEY != "CHANGE_ME" else random_string(64),
              prompt='Enter secret key.')
@click.option('--wiki-path',
              default=config.WIKI_PATH,
              prompt='Enter wiki data directory.',
              help='Wiki Directory (git repo)')
@click.option('--allow-anon',
              default=config.ALLOW_ANON,
              is_flag=True,
              prompt='Allow anonymous edits?')
@click.option('--registration-enabled',
              default=config.REGISTRATION_ENABLED,
              is_flag=True,
              prompt='Enable registration?')
@click.option('--cache-type',
              default=config.CACHE_TYPE,
              type=click.Choice([None, 'simple', 'redis', 'memcached']),
              prompt='Cache type?')
@click.option('--search-type',
              default=config.SEARCH_TYPE,
              type=click.Choice(['simple', 'whoosh', 'elasticsearch']),
              prompt='Search type?')
@click.option('--db-uri',
              default=config.DB_URI,
              prompt='Database URI? Examples: http://goo.gl/RyW0cl')
@click.pass_context
def setup(ctx, **kw):
    try:
        os.mkdir('/etc/realms3')
    except OSError:
        pass

    conf = {}

    for k, v in kw.items():
        conf[k.upper()] = v

    conf_path = config.update(conf)

    if conf['CACHE_TYPE'] == 'redis':
        prompt_and_invoke(ctx, setup_redis)
    elif conf['CACHE_TYPE'] == 'memcached':
        prompt_and_invoke(ctx, setup_memcached)

    if conf['SEARCH_TYPE'] == 'elasticsearch':
        prompt_and_invoke(ctx, setup_elasticsearch)
    elif conf['SEARCH_TYPE'] == 'whoosh':
        install_whoosh()

    green('Config saved to %s' % conf_path)


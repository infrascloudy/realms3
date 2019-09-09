import os
import click

from realms3 import config, create_app, db, __version__, cli, cache
from realms3.lib.util import random_string, in_virtualenv, green, yellow, red

config = config.conf
app = create_app()


def get_user():
    for name in ("SUDO_USER", "LOGNAME", "USER", "LNAME", "USERNAME"):
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
        v = click.prompt(
            p.prompt, p.default, p.hide_input, p.confirmation_prompt, p.type
        )
        kw[p.name] = v

    ctx.invoke(fn, **kw)


@app.cli.command()
@click.option("--site-title", default=config.SITE_TITLE, prompt="Enter site title.")
@click.option("--base_url", default=config.BASE_URL, prompt="Enter base URL.")
@click.option("--port", default=config.PORT, prompt="Enter port number.")
@click.option(
    "--secret-key",
    default=config.SECRET_KEY
    if config.SECRET_KEY != "CHANGE_ME"
    else random_string(64),
    prompt="Enter secret key.",
)
@click.option(
    "--wiki-path",
    default=config.WIKI_PATH,
    prompt="Enter wiki data directory.",
    help="Wiki Directory (git repo)",
)
@click.option(
    "--allow-anon",
    default=config.ALLOW_ANON,
    is_flag=True,
    prompt="Allow anonymous edits?",
)
@click.option(
    "--registration-enabled",
    default=config.REGISTRATION_ENABLED,
    is_flag=True,
    prompt="Enable registration?",
)
@click.option(
    "--cache-type",
    default=config.CACHE_TYPE,
    type=click.Choice([None, "simple", "redis", "memcached"]),
    prompt="Cache type?",
)
@click.option(
    "--search-type",
    default=config.SEARCH_TYPE,
    type=click.Choice(["simple", "whoosh", "elasticsearch"]),
    prompt="Search type?",
)
@click.option(
    "--db-uri",
    default=config.DB_URI,
    prompt="Database URI? Examples: http://goo.gl/RyW0cl",
)
@click.pass_context
def setup(ctx, **kw):
    try:
        os.mkdir("/etc/realms3")
    except OSError:
        pass

    conf = {}

    for k, v in kw.items():
        conf[k.upper()] = v

    conf_path = config.update(conf)

    if conf["CACHE_TYPE"] == "redis":
        prompt_and_invoke(ctx, setup_redis)
    elif conf["CACHE_TYPE"] == "memcached":
        prompt_and_invoke(ctx, setup_memcached)

    if conf["SEARCH_TYPE"] == "elasticsearch":
        prompt_and_invoke(ctx, setup_elasticsearch)
    elif conf["SEARCH_TYPE"] == "whoosh":
        install_whoosh()

    green("Config saved to %s" % conf_path)

    if not conf_path.startswith("/etc/realms3"):
        yellow("Note: You can move file to /etc/realms3/realms3.json")
        click.echo()

    yellow('Type "realms3 start" to start server')
    yellow('Type "realms3 dev" to start server in development mode')
    yellow("Full usage: realms3 --help")


@app.cli.command()
@click.option(
    "--cache-redis-host",
    default=getattr(config, "CACHE_REDIS_HOST", "127.0.0.1"),
    prompt="Redis host",
)
@click.option(
    "--cache-redis-port",
    default=getattr(config, "CACHE_REDIS_POST", 6379),
    prompt="Redis port",
    type=int,
)
@click.option(
    "--cache-redis-password",
    default=getattr(config, "CACHE_REDIS_PASSWORD", None),
    prompt="Redis password",
)
@click.option(
    "--cache-redis-db", default=getattr(config, "CACHE_REDIS_DB", 0), prompt="Redis db"
)
@click.pass_context
def setup_redis(ctx, **kw):
    conf = config.read()

    for k, v in kw.items():
        conf[k.upper()] = v

    config.update(conf)
    install_redis()


@app.cli.command()
@click.option(
    "--elasticsearch-url",
    default=getattr(config, "ELASTICSEARCH_URL", "http://127.0.0.1:9200"),
    prompt="Elasticsearch URL",
)
def setup_elasticsearch(**kw):
    conf = config.read()

    for k, v in kw.items():
        conf[k.upper()] = v

    config.update(conf)


cli.add_command(setup_redis)
cli.add_command(setup_elasticsearch)


def get_prefix():
    return sys.prefix

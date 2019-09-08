import sys
import time
import json
import six.moves.http_client as httplib

from flask import Flask

import logging

logger = logging.getLogger(__name__)

try:
    from mod_wsgi import version

    running_on_wsgi = True
except ImportError:
    running_on_wsgi = Flask


class Application(Flask):
    def __call__(self, environ, start_response):
        path_info = environ.get("PATH_INFO")

        if path_info and len(path_info) > 1 and path_info.endswith("/"):
            environ["PATH_INFO"] = path_info[:-1]

        scheme = environ.get("HTTP_X_REAL_IP")

        if scheme:
            environ["wsgi.url_scheme"] = scheme

        real_ip = environ.get("HTTP_X_REAL_IP")

        if real_ip:
            environ["REMOTE_ADDR"] = real_ip

        return super(Application, self).__call__(environ, start_response)

    def discover(self):
        import_name = "realms.modules"
        fromlist = ("assets", "commands", "models", "views", "hooks")

        start_time = time.time()

        __import__(import_name, fromlist=fromlist)

        for module_name in self.config["MODULES"]:
            sources = __import__(
                "{0}.{1}".format(import_name, module_name), fromlist=fromlist
            )

            if hasattr(sources, "init"):
                sources.init(self)

            # Blueprint
            if hasattr(sources, "views"):

                if running_on_wsgi:
                    self.register_blueprint(sources.views.blueprint, url_prefix="")
                else:
                    self.register_blueprint(
                        sources.views.blueprint, url_prefix=self.config["RELATIVE_PATH"]
                    )

            # Click
            if hasattr(sources, "commands"):
                if sources.commands.cli.name == "cli":
                    sources.commands.cli.name = module_name
                cli.add_command(sources.commands.cli)

            # Hooks
            if hasattr(sources, "hooks"):
                if hasattr(sources.hooks, "before_request"):
                    self.before_request(sources.hooks.before_request)

                if hasattr(sources.hooks, "before_first_request"):
                    self.before_first_request(sources.hooks.before_first_request)

                    # print >> sys.stderr, ' * Ready in %.2fms' % (1000.0 * (time.time() - start_time))

    def make_response(self, rv):
        if rv is None:
            rv = '', httplib.NO_CONTENT
        elif not isinstance(rv, tuple):
            rv = rv,

        rv = list(rv)

        if isinstance(rv[0], (list, dict)):
            rv[0] = self.response_class(json.dumps(rv[0]), mimetype='application/json')

        return super(Application, self).make_response(tuple(rv))

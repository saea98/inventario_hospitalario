"""Monta una sub-aplicación WSGI bajo un prefijo de URL (p. ej. /api/v1)."""


class PathPrefixMiddleware:
    def __init__(self, app, prefix: str, mount):
        self.app = app
        self.prefix = prefix.rstrip('/') or prefix
        self.mount = mount

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '') or '/'
        prefix = self.prefix
        if path == prefix or path.startswith(prefix + '/'):
            mount_environ = environ.copy()
            mount_environ['PATH_INFO'] = path[len(prefix):] or '/'
            mount_environ['SCRIPT_NAME'] = (environ.get('SCRIPT_NAME') or '') + prefix
            return self.mount(mount_environ, start_response)
        return self.app(environ, start_response)

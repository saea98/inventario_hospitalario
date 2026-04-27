from .settings import *  # noqa: F401,F403


# Base de datos aislada para CI/Jenkins (sin depender de PostgreSQL de ambiente).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Acelera hashing de contraseñas en pruebas.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


# Evita ejecutar migraciones históricas con SQL específico de PostgreSQL
# (p. ej. "DROP TABLE ... CASCADE"), incompatibles con SQLite en CI.
class DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

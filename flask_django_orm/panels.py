import itsdangerous
from flask import request, current_app, abort, g
from flask_debugtoolbar import module
from flask_debugtoolbar.panels import DebugPanel
from flask_debugtoolbar.utils import format_sql
from jinja2 import ChoiceLoader, PackageLoader

try:
    from django.db import connection
    from django.conf import settings
    from flask_django_orm import DjangoORM
except ImportError:
    django_orm_available = False
else:
    django_orm_available = True


_ = lambda x: x


def query_signer():
    return itsdangerous.URLSafeSerializer(current_app.config["SECRET_KEY"], salt="fdt-sql-query")


def is_select(statement):
    prefix = b"select" if isinstance(statement, bytes) else "select"
    return statement.lower().strip().startswith(prefix)


def dump_query(statement):
    if not is_select(statement):
        return None

    try:
        return query_signer().dumps(statement)
    except TypeError:
        return None


def load_query(data):
    try:
        statement = query_signer().loads(data)
    except (itsdangerous.BadSignature, TypeError):
        abort(406)

    # Make sure it is a select statement
    if not is_select(statement):
        abort(406)

    return statement


def extension_used():
    return "djangoorm" in current_app.extensions


def recording_enabled():
    return settings.DEBUG


def is_available():
    return extension_used() and recording_enabled()


def get_queries():
    return connection.queries

def dict_factory(cursor):
    d = []
    for idx in cursor.description:
        d.append(idx[0])
    return d

class DjangoORMDebugPanel(DebugPanel):
    """
    Panel that displays the time a query to the database took in seconds.
    """

    name = "DjangoORM"

    def __init__(self, jinja_env, context):
        DebugPanel.__init__(self, jinja_env, context=context)

        loader = ChoiceLoader([
            jinja_env.loader,
            PackageLoader(__name__, 'templates')
        ])
        self.jinja_env.loader = loader

    @property
    def has_content(self):
        return bool(get_queries()) or not is_available()

    def nav_title(self):
        return _("Django ORM")

    def nav_subtitle(self):
        count = len(get_queries())

        if not count and not is_available():
            return "Unavailable"

        return "%d %s" % (count, "query" if count == 1 else "queries")

    def title(self):
        return _("DjangORM queries")

    def url(self):
        return ""

    def content(self):

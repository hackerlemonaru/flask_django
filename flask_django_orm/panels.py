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

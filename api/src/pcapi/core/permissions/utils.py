from functools import wraps
import logging
import typing

from flask import Response
from flask import jsonify
from flask import request
from flask_login import current_user
from flask_login import login_required

from pcapi import settings
from pcapi.core.permissions.models import Permission
from pcapi.core.permissions.models import Permissions
from pcapi.core.permissions.models import Role
from pcapi.core.permissions.models import role_permission_table
from pcapi.models import db
from pcapi.models.api_errors import ApiErrors


logger = logging.getLogger(__name__)


def send_403_permission_needed(permission: Permissions) -> tuple[Response, int]:
    e = ApiErrors()
    e.add_error("global", "Permission requise")
    return jsonify(e.errors), 403


def permission_required(permission: Permissions) -> typing.Callable:
    def wrapper(func: typing.Callable) -> typing.Callable:
        @wraps(func)
        def wrapped(*args, **kwargs) -> typing.Union[tuple[Response, int], typing.Callable]:  # type: ignore[no-untyped-def]
            if not settings.IS_TESTING:
                current_roles = getattr(current_user, "groups", [])

                granted = db.session.query(
                    Role.query.filter(Role.name.in_(current_roles))
                    .join(role_permission_table)
                    .join(Permission)
                    .filter(Permission.name == permission.name)
                    .exists()
                ).scalar()

                if not granted:
                    logger.warning(
                        "user %s missed permission %s while trying to access %s",
                        current_user.email,
                        permission.name,
                        request.url,
                    )
                    return send_403_permission_needed(permission)

            return func(*args, **kwargs)

        return login_required(wrapped)

    return wrapper
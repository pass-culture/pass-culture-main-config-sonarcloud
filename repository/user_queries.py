import uuid
from uuid import UUID

from sqlalchemy import func, distinct

from models import User, UserSession, PcObject
from models.db import db


def find_user_by_email(email):
    return User.query.filter_by(email=email).first()


def find_user_by_reset_password_token(token):
    return User.query.filter_by(resetPasswordToken=token).first()


def find_users_by_department_and_date_range(date_max, date_min, department):
    query = db.session.query(User.id, User.dateCreated, User.departementCode)
    if department:
        query = query.filter(User.departementCode == department)
    if date_min:
        query = query.filter(User.dateCreated >= date_min)
    if date_max:
        query = query.filter(User.dateCreated <= date_max)
    result = query.order_by(User.dateCreated).all()
    return result


def find_users_stats_per_department(time_intervall):
    if time_intervall:
        return db.session.query(User.departementCode, func.date_trunc(time_intervall, User.dateCreated),
                                func.count(distinct(User.id))) \
            .filter(User.canBookFreeOffers == 'true') \
            .group_by(func.date_trunc(time_intervall, User.dateCreated), User.departementCode) \
            .order_by(func.date_trunc(time_intervall, User.dateCreated), User.departementCode) \
            .all()
    else:
        return db.session.query(User.departementCode, func.count(distinct(User.id))).filter(
            User.canBookFreeOffers == 'true').group_by(User.departementCode).order_by(User.departementCode).all()


def register_user_session(user_id: int, session_uuid: UUID):
    session = UserSession()
    session.userId = user_id
    session.uuid = session_uuid
    PcObject.check_and_save(session)


def delete_user_session(user_id: int, session_uuid: UUID):
    session = UserSession.query \
        .filter_by(userId=user_id, uuid=session_uuid) \
        .first()
    PcObject.delete(session)


def existing_user_session(user_id: int, session_uuid: UUID):
    session = UserSession.query \
        .filter_by(userId=user_id, uuid=session_uuid) \
        .first()
    return session is not None

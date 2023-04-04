from .features import Features


def clean_db(session):
    session.query(Features).delete()

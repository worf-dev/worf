from functools import wraps
import uuid


def valid_uuid(f=None, optional=False, field="user_id"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if kwargs.get(field) is None:
                    if optional:
                        return f(*args, **kwargs)
                    else:
                        return {"message": "UUID missing"}, 400
                uuid_value = uuid.UUID(kwargs[field])
            except ValueError:
                return {"message": "invalid UUID"}, 400
            kwargs[field] == uuid_value
            return f(*args, **kwargs)

        return decorated_function

    if f:
        return decorator(f)
    else:
        return decorator

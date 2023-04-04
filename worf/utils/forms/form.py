import datetime


class Field:
    default_validators = []

    @property
    def validators(self):
        return self.default_validators + self._validators

    def __init__(self, validators=None):
        if validators is None:
            validators = []
        self._validators = validators

    def validate(self, name, value, form):
        for validator in self.validators:
            result = validator(name, value, form)
            if result is None:
                errors, stop = [], False
            else:
                errors, value, stop = result
            if errors:
                return errors, value
            if stop:
                return [], value
        return [], value


class FormMeta(type):
    def __init__(cls, name, bases, namespace):
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                fields[key] = value
        cls.fields = fields
        super().__init__(name, bases, namespace)


class Form(metaclass=FormMeta):
    def __init__(self, data, is_update=False):
        self.is_update = is_update
        self._raw_data = data or {}

    @property
    def raw_data(self):
        return self._raw_data

    @property
    def valid_data(self):
        return self._valid_data

    @property
    def errors(self):
        return self._errors

    @raw_data.setter  # type: ignore
    def raw_data(self, data):
        self._raw_data = data or {}
        self._valid_data = {}
        self._errors = None

    def validate(self):
        data = {}
        errors = {}
        valid = True
        self._valid_data = None
        for name, field in self.fields.items():
            value = self.raw_data.get(name)
            if self.is_update and value is None:
                continue
            field_errors, value = field.validate(name, value, self)
            if field_errors:
                errors[name] = field_errors
                valid = False
            else:
                data[name] = value

        self._errors = errors
        if valid:
            self._valid_data = data
        return valid

    def format_errors(self):
        def fmt(errors, indent=0, ic="  "):
            s = ""
            for field, errors in errors.items():
                s += "{}{}:".format(ic * indent, field)
                for error in errors:
                    if isinstance(error, dict):
                        s += "\n" + fmt(error, indent=indent + 1, ic=ic)
                    else:
                        s += " {}\n".format(error)
            return s

        return fmt(self.errors)

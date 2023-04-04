import re
import uuid
import json
import base64


class ToLower:
    def __call__(self, name, value, form):
        return [], value.lower(), False


class JSON:
    def __call__(self, name, value, form):
        try:
            d = json.loads(value)
            return [], d, False
        except:
            return ["invalid json"], None, True


class Regex:
    def __init__(self, regex):
        self.regex = re.compile(regex)

    def __call__(self, name, value, form):
        if not self.regex.match(value):
            return ["regex does not match"], None, True


class Optional:
    def __init__(self, default=None, validate_default=False):
        self.default = default
        self.validate_default = validate_default

    def __call__(self, name, value, form):
        if value is None or (isinstance(value, (str, bytes)) and not value):
            return [], self.default, not self.validate_default


class List:
    def __init__(self, validators=None):
        if validators is None:
            validators = []
        self.validators = validators

    def __call__(self, name, value, form):
        if not isinstance(value, (list, tuple)):
            return ["not a list"], None, True
        if not self.validators:
            return [], value, False
        l = []
        for elem in value:
            for validator in self.validators:
                result = validator(name, elem, form)
                if result is None:
                    errors, stop = [], False
                else:
                    errors, elem, stop = result
                if errors:
                    return errors, elem, stop
            l.append(elem)
        return [], l, False


class Required:
    def __call__(self, name, value, form):
        if value is None:
            return ["is required"], None, True


class EMail:
    regex = re.compile(r"^[^\@]+\@[^\@]+\.[\w]+$")

    def __call__(self, name, value, form):
        if not value or not self.regex.match(value):
            return ["invalid e-mail"], None, True


class Length:
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __call__(self, name, value, form):
        if (
            self.min is not None
            and len(value) < self.min
            or self.max is not None
            and len(value) > self.max
        ):
            return (
                [
                    "invalid length (min: {min}, max: {max})".format(
                        min=self.min, max=self.max
                    )
                ],
                None,
                True,
            )


class Binary:
    def __call__(self, name, value, form):
        try:
            return [], base64.b64decode(value), False
        except:
            return (["invalid encoding"], None, True)  # continue validation


class Type:
    type = object

    def __init__(self, convert=False):
        self.convert = convert

    def __call__(self, name, value, form):
        err = (
            ["not of type: {type}".format(type=self.type.__name__.lower())],
            None,
            True,
        )
        if self.convert:
            try:
                value = self.type(value)
            except ValueError:
                return err
        if not isinstance(value, self.type):
            return err
        return [], value, False


class String(Type):
    type = str


class Boolean(Type):
    type = bool


class Dict(Type):
    type = dict


class Integer(Type):
    type = int

    def __init__(self, *args, min=None, max=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.min = min
        self.max = max

    def __call__(self, name, value, form):
        result = super().__call__(name, value, form)
        if result:
            errors, value, stop = result
            if errors:
                return result
        if (
            self.min is not None
            and value < self.min
            or self.max is not None
            and value > self.max
        ):
            return (
                [
                    "out of bounds (min: {min}, max: {max})".format(
                        min=self.min if self.min is not None else "",
                        max=self.max if self.max is not None else "",
                    )
                ],
                None,
                True,
            )
        return result


class UUID:
    def __call__(self, name, value, form):
        try:
            value = uuid.UUID(value)
        except ValueError:
            return ["not a UUID"], None, True
        return [], value, False


class DateTime:
    def __init__(self, format="%Y-%m-%dT%H:%M:%SZ"):
        self.format = format

    def __call__(self, name, value, form):
        try:
            value = datetime.datetime.strptime(value, self.format)
        except ValueError:
            return (
                ["does not match format '{format}'".format(format=self.format)],
                None,
                True,
            )


class Choices:
    def __init__(self, choices):
        self.choices = choices

    def __call__(self, name, value, form):
        if not value in self.choices:
            return (
                [
                    "not a valid choice (choices: {choices})".format(
                        choices=self.choices
                    )
                ],
                None,
                True,
            )


class Subform:
    def __init__(self, FormClass):
        self.FormClass = FormClass

    def __call__(self, name, value, form):
        form = self.FormClass(value or {})
        if form.validate():
            return [], value, False
        else:
            return [form.errors], None, True


class Equal:
    def __init__(self, value, message=None):
        self.value = value
        self.message = message or "form.not-equal"

    def __call__(self, name, value, form):
        if value != self.value:
            return [self.message], None, True

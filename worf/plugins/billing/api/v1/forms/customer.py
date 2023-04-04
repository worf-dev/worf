from worf.utils.forms import Form, Field, Optional
from .country_code import CountryCode
from .vat_id import VatId

from worf.utils.forms.validators import (
    String,
    ToLower,
    DateTime,
    Required,
    Integer,
    Boolean,
    Choices,
    UUID,
    EMail,
    Length,
)

from worf.settings import settings


class CustomerForm(Form):
    name = Field([Required(), String(), Length(min=2, max=100)])
    additional_name = Field([Optional(), String(), Length(min=2, max=100)])
    street = Field([Required(), String(), Length(min=2, max=100)])
    city = Field([Required(), String(), Length(min=2, max=100)])
    zip_code = Field([Required(), String(), Length(min=4, max=10)])
    country = Field([Required(), String(), Length(min=2, max=2), CountryCode()])
    additional_address = Field([Optional(), String(), Length(min=2, max=100)])
    vat_id = Field([Optional(), VatId()])
    phone = Field([Optional(), String(), Length(min=2, max=20)])  # to do: add validator
    email = Field([Optional(), String(), EMail()])
    website = Field(
        [Optional(), String(), Length(min=2, max=40)]
    )  # to do: add validator

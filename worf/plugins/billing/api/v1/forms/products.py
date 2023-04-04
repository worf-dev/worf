from worf.utils.forms import Form, Field
from worf.utils.forms.validators import String, Optional, Length


class ProductsForm(Form):
    access_code = Field([Optional(), String(), Length(max=40)])

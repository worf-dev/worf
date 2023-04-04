from worf.utils.forms import Form, Field
from worf.utils.forms.validators import List, String, Length


class FeaturesForm(Form):
    features = Field([List([String(), Length(max=256)])])

from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ....models import Product
from ..forms.products import ProductsForm

from sqlalchemy.orm import joinedload

from worf.api.decorators.user import authorized


class Products(Resource):

    """
    Return information about all available products.
    """

    @authorized(scopes=("admin",))
    def get(self):
        """
        Return all products.
        """

        form = ProductsForm(request.args)

        if not form.validate():
            return {"message": self.t("invalid-data"), "errors": form.errors}, 400

        access_code = form.valid_data.get("access_code")

        with settings.session() as session:
            products = session.query(Product).options(joinedload(Product.prices)).all()
        return (
            {
                "data": [
                    product.export(
                        access_code=access_code, for_superuser=request.user.superuser
                    )
                    for product in products
                ]
            },
            200,
        )

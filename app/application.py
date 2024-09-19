from fastapi import routing

from app.api.routers.public.public_router_v10 import public_router_v10
from app.base_application.application import OrnamentApplication


class ServiceApplication(OrnamentApplication):
    def get_internal_routers(self) -> list[routing.APIRouter]:
        """
            Implement internal routers setup here.
        """
        return []

    def get_public_routers(self) -> list[routing.APIRouter]:
        routers = [public_router_v10]
        return routers

    def get_additional_middlewares(self) -> list[type]:
        """
            Implement additional middlewares setup here.
        """
        return []


application = ServiceApplication().create_app()

import logging
import random
import string
import time

import sentry_sdk
from fastapi import routing
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarlleteHTTPException
from abc import ABC, abstractmethod

from app.config.config import settings
from app.config.constants import ms_multiplier
from app.redis.cluster import OrnamentRedisCluster
from app.sentry.setup import init_sentry

logger = logging.getLogger(__name__)

rc = OrnamentRedisCluster()


class OrnamentApplication(ABC):

    def get_service_name(self):
        return settings.service_name

    def snake_case_to_text(self, snake_case_string):
        words = snake_case_string.split('_')
        capitalized_words = [word.capitalize() for word in words]
        regular_text = ' '.join(capitalized_words)
        return regular_text

    def create_app(self) -> FastAPI:
        public_server = {
            "url": settings.swagger_public_api_url,
            "description": "Public API",
        }
        internal_server = {
            "url": settings.swagger_internal_api_url,
            "description": "Internal API",
        }

        service_name = self.get_service_name()

        """Init fastapi app."""
        application = FastAPI(
            docs_url=f"/{service_name}/internal/swagger/",
            redoc_url=f"/{service_name}/internal/redoc/",
            openapi_url=f"/{service_name}/internal/openapi.json",
            title=f"{self.snake_case_to_text(service_name)}",
            version=settings.version,
            swagger_ui_parameters={
                "syntaxHighlight.theme": "monokai",
                "docExpansion": "none",
                "defaultModelsExpandDepth": 0,
            },
            servers=[public_server, internal_server],
        )

        public_routers = self.get_public_routers()
        internal_routers = self.get_internal_routers()
        for public_key_value_router in public_routers:
            application.include_router(public_key_value_router)
        for internal_key_value_router in internal_routers:
            application.include_router(internal_key_value_router)

        application.add_middleware(SentryAsgiMiddleware)

        @application.middleware("http")
        async def log_requests(request: Request, call_next):
            idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            logger.info(f"rid={idem} start request path={request.url.path}")
            start_time = time.time()

            response = await call_next(request)

            process_time = (time.time() - start_time) * ms_multiplier
            formatted_process_time = "{0:.2f}".format(process_time)
            logger.info(
                f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}"
            )

            return response

        @application.exception_handler(StarlleteHTTPException)
        async def sentry_client_exception_handler(request, exc):
            sentry_sdk.capture_exception(exc)
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder({"detail": exc.detail}),
            )

        @application.exception_handler(Exception)
        async def sentry_client_exception_handler(request, exc):
            sentry_sdk.capture_exception(exc)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder({"detail": str(exc)}),
            )

        @application.exception_handler(RequestValidationError)
        async def sentry_api_model_validation_error_handler(
                request: Request, exc: RequestValidationError
        ):
            sentry_sdk.capture_exception(exc)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
            )

        @application.middleware("http")
        async def redis_connect_middleware(request: Request, call_next):
            start_time = time.time()
            if not rc.connect:
                rc.refresh_connect()

            request.state.ornament_redis_cluster = rc
            request.state.redis_connect = rc.connect
            response = await call_next(request)
            response.headers["X-Process-Time"] = str(time.time() - start_time)
            return response

        for middleware in self.get_additional_middlewares():
            application.add_middleware(middleware)

        init_sentry()

        return application


    @abstractmethod
    def get_public_routers(self) -> list[routing.APIRouter]:
        pass

    @abstractmethod
    def get_internal_routers(self) -> list[routing.APIRouter]:
        pass

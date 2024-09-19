from fastapi_camelcase import CamelModel
from pydantic import BaseModel


class OrnamentBase(CamelModel, BaseModel):
    class Config:
        orm_mode = True

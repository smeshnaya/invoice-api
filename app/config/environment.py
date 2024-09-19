from enum import Enum


class Environment(Enum):
    local = "local"
    development = "development"
    testing = "testing"
    stage = "stage"
    production = "production"

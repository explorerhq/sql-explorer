import factory
from explorer import models


class SimpleQueryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Query

    title = "My simple query"
    sql = "SELECT 1+1 AS TWO"  # same result in postgres and sqlite
    description = "Doin' math"
    created_by = "Factory boy"
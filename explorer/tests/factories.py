import factory
from explorer import models


class SimpleQueryFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Query

    title = factory.Sequence(lambda n: 'My siple query %s' % n)
    sql = "SELECT 1+1 AS TWO"  # same result in postgres and sqlite
    description = "Doin' math"
    created_by_user_id = 1


class QueryLogFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.QueryLog

    sql = "SELECT 2+2 AS FOUR"
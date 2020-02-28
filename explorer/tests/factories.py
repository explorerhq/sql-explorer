import factory
from django.conf import settings

from explorer import models


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: 'User %03d' % n)
    is_staff = True


class SimpleQueryFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Query

    title = factory.Sequence(lambda n: 'My simple query %s' % n)
    sql = "SELECT 1+1 AS TWO"  # same result in postgres and sqlite
    description = "Doin' math"
    connection = "default"
    created_by_user = factory.SubFactory(UserFactory)


class QueryLogFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.QueryLog

    sql = "SELECT 2+2 AS FOUR"

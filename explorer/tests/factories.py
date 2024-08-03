from django.conf import settings

from factory import Sequence, SubFactory, LazyFunction
from factory.django import DjangoModelFactory

from explorer.models import Query, QueryLog
from explorer.ee.db_connections.utils import default_db_connection_id


class UserFactory(DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = Sequence(lambda n: "User %03d" % n)
    is_staff = True


class SimpleQueryFactory(DjangoModelFactory):

    class Meta:
        model = Query

    title = Sequence(lambda n: f"My simple query {n}")
    sql = "SELECT 1+1 AS TWO"  # same result in postgres and sqlite
    description = "Doin' math"
    created_by_user = SubFactory(UserFactory)
    database_connection_id = LazyFunction(default_db_connection_id)


class QueryLogFactory(DjangoModelFactory):

    class Meta:
        model = QueryLog

    sql = "SELECT 2+2 AS FOUR"
    database_connection_id = LazyFunction(default_db_connection_id)

# -*- coding: utf-8 -*-
from django.conf import settings
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

from explorer.models import Query, QueryLog


class UserFactory(DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = Sequence(lambda n: 'User %03d' % n)
    is_staff = True


class SimpleQueryFactory(DjangoModelFactory):

    class Meta:
        model = Query

    title = Sequence(lambda n: f'My simple query {n}')
    sql = "SELECT 1+1 AS TWO"  # same result in postgres and sqlite
    description = "Doin' math"
    connection = "default"
    created_by_user = SubFactory(UserFactory)


class QueryLogFactory(DjangoModelFactory):

    class Meta:
        model = QueryLog

    sql = "SELECT 2+2 AS FOUR"

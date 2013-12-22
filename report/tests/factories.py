import factory
from report import models

class SimpleReportFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Report

    title = "My simple report"
    sql = "SELECT 1+1 AS TWO" #same result in postgres and sqlite
    description = "Doin' math"
    created_by = "Factory boy"
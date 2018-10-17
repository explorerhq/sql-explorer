from celery import group
from celery.utils.log import get_task_logger
from django.core.management.base import BaseCommand
from django.db.models import F, Q

from explorer.models import Query, FTPExport
from explorer.tasks import snapshot_query_on_bucket


logger = get_task_logger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info("Starting query snapshots...")
        qs_bucket = Query.objects.exclude(
            Q(bucket__exact='') |
            Q(bucket__isnull=True)
        ).annotate(
            query_id=F('id'), 
            query_priority=F('priority')
        ).values(
            'query_id',
            'query_priority'
        )
        qs_ftp = FTPExport.objects.all().annotate(
            query_id=F('query__id'),
            query_priority=F('query__priority')
        ).values(
            'query_id',
            'query_priority'
        )
        
        total_ids = list(qs_bucket) + list(qs_ftp)
        mandatory_ids = {x["query_id"] for x in total_ids if x["query_priority"] is True}
        not_mandatory_ids = {x["query_id"] for x in total_ids if x["query_priority"] is False}
        logger.info("Found %s queries to snapshot. Creating snapshot tasks..." % len(total_ids))
        high_priority_group = group([snapshot_query_on_bucket.s(qid) for qid in mandatory_ids])()
        # this forces the first group to check for the result and until this function does not finish,
        # the secondary group does not start.
        high_priority_group.get()
        group([snapshot_query_on_bucket.s(qid) for qid in not_mandatory_ids])()

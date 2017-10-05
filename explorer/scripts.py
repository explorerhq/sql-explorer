from celery.utils.log import get_task_logger

from explorer.models import Query, FTPExport
from explorer.tasks import snapshot_query_on_bucket

logger = get_task_logger(__name__)


def publish_queries():
    logger.info("Starting query snapshots...")
    qs_bucket = Query.objects.exclude(bucket__exact='').values_list('id', flat=True)
    qs_ftp = FTPExport.objects.all().values_list('query__id', flat=True)
    total_ids = set(list(qs_bucket)+list(qs_ftp))
    logger.info("Found %s queries to snapshot. Creating snapshot tasks..." % len(total_ids))
    for qid in total_ids:
        snapshot_query_on_bucket.delay(qid)
    logger.info("Done creating tasks.")

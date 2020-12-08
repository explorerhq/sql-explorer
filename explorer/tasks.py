from datetime import date, datetime, timedelta
import random
import string

from django.core.mail import send_mail
from django.core.cache import cache
from django.db import DatabaseError

from explorer import app_settings
from explorer.exporters import get_exporter_class
from explorer.models import Query, QueryLog

if app_settings.ENABLE_TASKS:
    from celery import task
    from celery.utils.log import get_task_logger
    from explorer.utils import s3_upload
    logger = get_task_logger(__name__)
else:
    from explorer.utils import noop_decorator as task
    import logging
    logger = logging.getLogger(__name__)


@task
def execute_query(query_id, email_address):
    q = Query.objects.get(pk=query_id)
    send_mail('[SQL Explorer] Your query is running...',
              f'{q.title} is running and should be in your inbox soon!',
              app_settings.FROM_EMAIL,
              [email_address])

    exporter = get_exporter_class('csv')(q)
    random_part = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        ) for _ in range(20)
    )
    try:
        url = s3_upload(f'{random_part}.csv', exporter.get_file_output())
        subj = f'[SQL Explorer] Report "{q.title}" is ready'
        msg = f'Download results:\n\r{url}'
    except DatabaseError as e:
        subj = f'[SQL Explorer] Error running report {q.title}'
        msg = f'Error: {e}\nPlease contact an administrator'
        logger.warning(f'{subj}: {e}')
    send_mail(subj, msg, app_settings.FROM_EMAIL, [email_address])


@task
def snapshot_query(query_id):
    try:
        logger.info(f"Starting snapshot for query {query_id}...")
        q = Query.objects.get(pk=query_id)
        exporter = get_exporter_class('csv')(q)
        k = 'query-{}/snap-{}.csv'.format(
            q.id,
            date.today().strftime('%Y%m%d-%H:%M:%S')
        )
        logger.info(f"Uploading snapshot for query {query_id} as {k}...")
        url = s3_upload(k, exporter.get_file_output())
        logger.info(
            f"Done uploading snapshot for query {query_id}. URL: {url}"
        )
    except Exception as e:
        logger.warning(
            f"Failed to snapshot query {query_id} ({e}). Retrying..."
        )
        snapshot_query.retry()


@task
def snapshot_queries():
    logger.info("Starting query snapshots...")
    qs = Query.objects.filter(snapshot=True).values_list('id', flat=True)
    logger.info(
        f"Found {len(qs)} queries to snapshot. Creating snapshot tasks..."
    )
    for qid in qs:
        snapshot_query.delay(qid)
    logger.info("Done creating tasks.")


@task
def truncate_querylogs(days):
    qs = QueryLog.objects.filter(
        run_at__lt=datetime.now() - timedelta(days=days)
    )
    logger.info(
        f'Deleting {qs.count} QueryLog objects older than {days} days.'
    )
    qs.delete()
    logger.info('Done deleting QueryLog objects.')


@task
def build_schema_cache_async(connection_alias):
    from .schema import build_schema_info, connection_schema_cache_key
    ret = build_schema_info(connection_alias)
    cache.set(connection_schema_cache_key(connection_alias), ret)
    return ret

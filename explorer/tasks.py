from datetime import date, datetime, timedelta
import random
import string

from celery import group
from django.core.mail import send_mail
from django.db.models import F

from explorer import app_settings
from explorer.exporters import get_exporter_class
from explorer.models import Query, QueryLog, FTPExport

if app_settings.ENABLE_TASKS:
    from celery import task
    from celery.utils.log import get_task_logger
    from explorer.utils import s3_upload, moni_s3_upload, moni_s3_transfer_file_to_ftp

    logger = get_task_logger(__name__)
else:
    from explorer.utils import noop_decorator as task
    import logging

    logger = logging.getLogger(__name__)


@task
def execute_query(query_id, email_address):
    q = Query.objects.get(pk=query_id)
    exporter = get_exporter_class('csv')(q)
    random_part = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    url = s3_upload('%s.csv' % random_part, exporter.get_file_output())

    subj = '[SQL Explorer] Report "%s" is ready' % q.title
    msg = 'Download results:\n\r%s' % url

    send_mail(subj, msg, app_settings.FROM_EMAIL, [email_address])


@task
def snapshot_query(query_id):
    try:
        logger.info("Starting snapshot for query %s..." % query_id)
        q = Query.objects.get(pk=query_id)
        exporter = get_exporter_class('csv')(q)
        k = 'query-%s.snap-%s.csv' % (q.id, date.today().strftime('%Y%m%d-%H:%M:%S'))
        logger.info("Uploading snapshot for query %s as %s..." % (query_id, k))
        url = s3_upload(k, exporter.get_file_output())
        logger.info("Done uploading snapshot for query %s. URL: %s" % (query_id, url))
    except Exception as e:
        logger.warning("Failed to snapshot query %s (%s). Retrying..." % (query_id, e.message))
        snapshot_query.retry()


@task
def snapshot_queries():
    logger.info("Starting query snapshots...")
    qs = Query.objects.filter(snapshot=True).values_list('id', flat=True)
    logger.info("Found %s queries to snapshot. Creating snapshot tasks..." % len(qs))
    for qid in qs:
        snapshot_query.delay(qid)
    logger.info("Done creating tasks.")


@task
def truncate_querylogs(days):
    qs = QueryLog.objects.filter(run_at__lt=datetime.now() - timedelta(days=days))
    logger.info('Deleting %s QueryLog objects older than %s days.' % (qs.count, days))
    qs.delete()
    logger.info('Done deleting QueryLog objects.')


@task
def snapshot_query_on_bucket(query_id):
    try:
        import time
        logger.info("Starting snapshot for query %s..." % query_id)
        q = Query.objects.get(pk=query_id)
        q_name = q.slug if q.slug else q.id
        exporter = get_exporter_class('csv')(q)
        k = '%s-%s.csv' % (q_name, date.today().strftime('%Y%m%d'))
        file_output = exporter.get_file_output(encoding=q.encoding)
        if q.bucket != '':
            logger.info("Uploading snapshot for query %s as %s..." % (query_id, k))
            url = moni_s3_upload(k, file_output, q.bucket)
            logger.info("Done uploading snapshot for query %s. URL: %s" % (query_id, url))
        # sends the file of the query via all the FTP exports
        for ftp_export in q.ftpexport_set.all():
            moni_s3_transfer_file_to_ftp(ftp_export, file_output, k, ftp_export.passive)
            time.sleep(2)
    except Exception as e:
        logger.warning("Failed to snapshot query %s (%s)." % (query_id, e.message))
    return datetime.now()


@task
def snapshot_queries_on_bucket():
    logger.info("Starting query snapshots...")
    qs_bucket = Query.objects.exclude(bucket__exact='').annotate(query_id=F('id'),
                                                                 query_priority=F('priority')).values(
        'query_id',
        'query_priority')
    qs_ftp = FTPExport.objects.all().annotate(query_id=F('query__id'),
                                              query_priority=F('query__priority')).values('query_id',
                                                                                          'query_priority')
    total_ids = list(qs_bucket) + list(qs_ftp)
    mandatory_ids = {x["query_id"] for x in total_ids if x["query_priority"] is True}
    not_mandatory_ids = {x["query_id"] for x in total_ids if x["query_priority"] is False}
    logger.info("Found %s queries to snapshot. Creating snapshot tasks..." % len(total_ids))
    high_priority_group = group([snapshot_query_on_bucket.s(qid) for qid in mandatory_ids])()
    # this forces the first group to check for the result and until this function does not finish,
    # the secondary group does not start.
    high_priority_group.get()
    group([snapshot_query_on_bucket.s(qid) for qid in not_mandatory_ids])()

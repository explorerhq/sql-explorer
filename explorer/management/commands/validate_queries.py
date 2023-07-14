from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from ...models import Query

class Command(BaseCommand):
    help = "Run all SQL Explorer queries and print out any errors that occurred."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int)
        parser.add_argument("--exclude", nargs="*", type=int, default=[])

    def handle(self, *args, **options):
        with ThreadPoolExecutor() as executor:
            for future in as_completed([
                executor.submit(_check_if_query_runs, query=query)
                for query in 
                Query.objects.exclude(pk__in=options["exclude"]).iterator()
            ]):
                query_id, error = future.result()
                if error is None:
                    self.stdout.write(
                        self.style.SUCCESS(f"Query {query_id} ran successfully")
                    )
                else:
                    self.stderr.write(
                        self.style.ERROR(f"Query {query_id} finished with error: {error}")
                    )


def _check_if_query_runs(query: Query) -> Tuple[int, Optional[str]]:
    try:
        query.execute_with_logging(executing_user=None)
        return query.pk, None
    except Exception as e:
        return query.pk, str(e)

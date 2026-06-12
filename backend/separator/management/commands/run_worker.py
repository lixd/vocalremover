import logging

from django.core.management.base import BaseCommand

from separator.worker import Worker


class Command(BaseCommand):
    help = "Run the audio separation worker"

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds between DB polls (default: 2.0)",
        )

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        worker = Worker(poll_interval=options["poll_interval"])
        worker.run()

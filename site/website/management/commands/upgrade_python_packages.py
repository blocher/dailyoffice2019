from django.core.management.base import BaseCommand
import importlib.metadata
from subprocess import call


class Command(BaseCommand):
    help = "Update all python packages and write to requirements.txt"

    def handle(self, *args, **options):
        packages = [dist.metadata["Name"] for dist in importlib.metadata.distributions()]
        call("pip install --upgrade --upgrade-strategy=eager " + " ".join(packages), shell=True)
        call("pip freeze > ../requirements.txt", shell=True)

from django.core.management.base import BaseCommand
import pkg_resources
from subprocess import call


class Command(BaseCommand):
    help = "Update all python packages and write to requirements.txt"

    def handle(self, *args, **options):
        packages = [dist.project_name for dist in pkg_resources.working_set]
        call("pip install --upgrade --upgrade-strategy=eager " + " ".join(packages), shell=True)
        call("pip freeze > ../requirements.txt", shell=True)

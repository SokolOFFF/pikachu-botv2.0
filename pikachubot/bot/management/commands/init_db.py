from bot.models import Theme, CSV
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        themes = ["good morning!",
                  "good night!",
                  "go sleep, dear!",
                  "how are you?",
                  "you are awesome!",
                  "i miss you :<",
                  "*confusedd*",
                  "love you! <3",
                  "don't be upset! :)",
                  "hugggggs",
                  "just random cute picture :>"]

        short_themes = ["GM", "GN", "GSD", "HAU", "YAA", "IMU", "CONF", "LU", "DBU", "HUG", "JRCP"]

        for i in range(len(themes)):
            th = Theme(name=themes[i], short_name=short_themes[i])
            th.save()
        csv = CSV()
        csv.save()
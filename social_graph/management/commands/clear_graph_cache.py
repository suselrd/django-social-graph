# coding=utf-8
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        from social_graph import Graph
        Graph().clear_cache()

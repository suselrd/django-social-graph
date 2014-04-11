# coding=utf-8
from django.dispatch import Signal

object_created = Signal(providing_args=['instance'])
object_updated = Signal(providing_args=['instance'])
object_deleted = Signal(providing_args=['instance'])
object_visited = Signal(providing_args=['instance'])

edge_created = Signal(providing_args=['instance'])
edge_updated = Signal(providing_args=['instance'])
edge_deleted = Signal(providing_args=['instance'])


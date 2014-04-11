# coding=utf-8
from django.db import models
from social_graph.decorators import crud_aware


@crud_aware
class A(models.Model):
    a = models.IntegerField()


class B(models.Model):
    b = models.IntegerField()
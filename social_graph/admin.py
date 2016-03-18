# coding=utf-8
from django.contrib import admin
from .models import EdgeType, EdgeTypeAssociation


admin.site.register(EdgeType)
admin.site.register(EdgeTypeAssociation)


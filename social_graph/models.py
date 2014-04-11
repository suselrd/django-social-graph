# coding=utf-8
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from social_graph.fields import JSONField


class EdgeType(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    read_as = models.CharField(_('read as'), max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name = _('Edge type')
        verbose_name_plural = _('Edge types')

    def __unicode__(self):
        return self.name

    def setting_name(self):
        return self.name.upper()


class EdgeTypeAssociation(models.Model):
    direct = models.ForeignKey(EdgeType, unique=True, related_name='is_direct_in')
    inverse = models.ForeignKey(EdgeType, unique=True, related_name='is_inverse_in')

    def __unicode__(self):
        return ("%(direct)s <-> %(inverse)s"
                % {'direct': self.direct.name,
                   'inverse': self.inverse.name})


class Edge(models.Model):
    # fromNode field
    fromNode_type = models.ForeignKey(ContentType,
                                      verbose_name=_('from node type'),
                                      related_name="from_node_type_set_for_%(class)s")
    fromNode_pk = models.TextField(_('fromNode ID'))
    fromNode = generic.GenericForeignKey(ct_field="fromNode_type", fk_field="fromNode_pk")

    # toNode field
    toNode_type = models.ForeignKey(ContentType,
                                    verbose_name=_('to node type'),
                                    related_name="to_node_type_set_for_%(class)s")
    toNode_pk = models.TextField(_('toNode ID'))
    toNode = generic.GenericForeignKey(ct_field="toNode_type", fk_field="toNode_pk")

    # edge attributes
    type = models.ForeignKey(EdgeType)
    attributes = JSONField(_('attributes'), default='{}')

    # edge metadata
    time = models.DateTimeField(_('time'), auto_now_add=True)
    site = models.ForeignKey(Site, default=settings.SITE_ID, verbose_name=_('site'), related_name='edges')
    auto = models.BooleanField(_('auto created'), default=False)

    class Meta:
        ordering = ['-time']

    def __unicode__(self):
        return (_('%(from)s %(verb)s %(to)s')
                % {'from': self.fromNode,
                   'verb': self.type.read_as,
                   'to': self.toNode})


class EdgeCount(models.Model):
    # fromNode field
    fromNode_type = models.ForeignKey(ContentType,
                                      verbose_name=_('from node type'))
    fromNode_pk = models.TextField(_('fromNode ID'))
    fromNode = generic.GenericForeignKey(ct_field="fromNode_type", fk_field="fromNode_pk")

    # edge attributes
    type = models.ForeignKey(EdgeType)

    # count
    count = models.IntegerField(_('count'), default=0)

    def __unicode__(self):
        return (_('%(from)s has %(count)d %(type)s edge(s)')
                % {
            'from': self.fromNode,
            'count': self.count,
            'type': self.type
        })
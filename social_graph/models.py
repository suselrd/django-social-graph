# coding=utf-8
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.db import models
from django.utils.translation import ugettext_lazy as _
from social_graph.fields import JSONField


class EdgeTypeManager(models.Manager):
    # Cache to avoid re-looking up EdgeType objects all over the place.
    _cache = {}

    def get(self, *args, **kwargs):
        et = None
        if 'id' in kwargs:
            try:
                et = self.__class__._cache[self.db][kwargs['id']]
            except KeyError:
                pass
        elif 'pk' in kwargs:
            try:
                et = self.__class__._cache[self.db][kwargs['pk']]
            except KeyError:
                pass
        elif 'name' in kwargs:
            try:
                et = self.__class__._cache[self.db][kwargs['name']]
            except KeyError:
                pass

        if et is None:
            et = super(EdgeTypeManager, self).get(*args, **kwargs)
            self._add_to_cache(self.db, et)
        return et

    def _add_to_cache(self, using, et):
        self.__class__._cache.setdefault(using, {})[et.id] = et
        self.__class__._cache.setdefault(using, {})[et.name] = et

    def rem_from_cache(self, using, et):
        try:
            del self.__class__._cache.setdefault(using, {})[et.id]
            del self.__class__._cache.setdefault(using, {})[et.name]
        except KeyError:
            pass

    def clear_cache(self):
        """
        Clear out the edge-type cache.
        """
        self.__class__._cache.clear()


class EdgeType(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    read_as = models.CharField(_('read as'), max_length=100)

    objects = EdgeTypeManager()

    class Meta:
        ordering = ['name']
        verbose_name = _('Edge type')
        verbose_name_plural = _('Edge types')

    def __unicode__(self):
        return self.name

    def setting_name(self):
        return self.name.upper()

    def delete(self, using=None):
        self.__class__.objects.rem_from_cache(using, self)
        super(EdgeType, self).delete(using)


class EdgeTypeAssociationManager(models.Manager):
    # Cache to avoid re-looking up EdgeTypeAssociation objects all over the place.
    _cache = {}
    _direct_cache = {}
    _inverse_cache = {}

    def get(self, *args, **kwargs):
        eta = None
        if 'id' in kwargs:
            try:
                eta = self.__class__._cache[self.db][kwargs['id']]
            except KeyError:
                pass
        elif 'pk' in kwargs:
            try:
                eta = self.__class__._cache[self.db][kwargs['pk']]
            except KeyError:
                pass
        if eta is None:
            eta = super(EdgeTypeAssociationManager, self).get(*args, **kwargs)
            self._add_to_cache(self.db, eta)
        return eta

    def get_for_direct_edge_type(self, et):
        try:
            eta = self.__class__._direct_cache[self.db][et.id]
        except KeyError:
            eta = self.get(direct=et)
            self._add_to_cache(self.db, eta)
        return eta

    def get_for_inverse_edge_type(self, et):
        try:
            eta = self.__class__._inverse_cache[self.db][et.id]
        except KeyError:
            eta = self.get(inverse=et)
            self._add_to_cache(self.db, eta)
        return eta

    def _add_to_cache(self, using, eta):
        self.__class__._cache.setdefault(using, {})[eta.id] = eta
        self.__class__._direct_cache.setdefault(using, {})[eta.direct.id] = eta
        self.__class__._inverse_cache.setdefault(using, {})[eta.inverse.id] = eta

    def rem_from_cache(self, using, eta):
        try:
            del self.__class__._cache.setdefault(using, {})[eta.id]
            del self.__class__._direct_cache.setdefault(using, {})[eta.direct.id]
            del self.__class__._inverse_cache.setdefault(using, {})[eta.inverse.id]
        except KeyError:
            pass

    def clear_cache(self):
        """
        Clear out the edge-type-association cache.
        """
        self.__class__._cache.clear()


class EdgeTypeAssociation(models.Model):
    direct = models.ForeignKey(EdgeType, unique=True, related_name='is_direct_in')
    inverse = models.ForeignKey(EdgeType, unique=True, related_name='is_inverse_in')

    objects = EdgeTypeAssociationManager()

    def __unicode__(self):
        return ("%(direct)s <-> %(inverse)s"
                % {'direct': self.direct.name,
                   'inverse': self.inverse.name})

    def delete(self, using=None):
        self.__class__.objects.rem_from_cache(using, self)
        super(EdgeTypeAssociation, self).delete(using)


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

    objects = models.Manager()
    on_site = CurrentSiteManager()

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

    site = models.ForeignKey(Site, default=settings.SITE_ID, verbose_name=_('site'), related_name='edge_counters')

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __unicode__(self):
        return (_('%(from)s has %(count)d %(type)s edge(s)')
                % {
            'from': self.fromNode,
            'count': self.count,
            'type': self.type
        })

    class Meta:
        unique_together = ['fromNode_type', 'fromNode_pk', 'type', 'site']
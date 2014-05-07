# coding=utf-8
from django import forms
from django.forms.util import ErrorList
from . import Graph


class BaseEdgeForm(forms.Form):
    edge_origin = 'fromNode'
    edge_target = 'toNode'
    edge_type = 'type'
    edge_attributes = ['attribute', ]
    update = False

    _graph = Graph()

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=None, empty_permitted=False, update=None):
        super(BaseEdgeForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix,
                                           empty_permitted)
        if update is not None:
            self.update = update

    def get_etype(self):
        if not self.cleaned_data[self.edge_type]:
            raise Exception("Missing '%s' in cleaned_data dict" % self.edge_type)
        return self.cleaned_data[self.edge_type]

    def get_origin(self):
        if not self.cleaned_data[self.edge_origin]:
            raise Exception("Missing '%s' in cleaned_data dict" % self.edge_origin)
        return self.cleaned_data[self.edge_origin]

    def get_target(self):
        if not self.cleaned_data[self.edge_target]:
            raise Exception("Missing '%s' in cleaned_data dict" % self.edge_target)
        return self.cleaned_data[self.edge_target]

    def get_attributes(self):
        attributes = {}
        for edge_attribute in self.edge_attributes:
            value = self.cleaned_data.setdefault(edge_attribute, None)
            if value is not None:
                attributes.update({edge_attribute: value})
        return attributes

    def save(self):
        if self.update:
            suitable_method = self._graph.edge_change
        else:
            suitable_method = self._graph.edge_add

        return suitable_method(self.get_origin(),
                               self.get_target(),
                               self.get_etype(),
                               attributes=self.get_attributes())


class SpecificEdgeTypeMixin(object):

    @property
    def etype(self):
        raise NotImplementedError('%s must have an etype' % self.__class__)

    def get_etype(self):
        return self.etype


class SpecificTypeEdgeForm(SpecificEdgeTypeMixin, BaseEdgeForm):
    pass


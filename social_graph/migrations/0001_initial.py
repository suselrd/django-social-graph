# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EdgeType'
        db.create_table(u'social_graph_edgetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('read_as', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'social_graph', ['EdgeType'])

        # Adding model 'EdgeTypeAssociation'
        db.create_table(u'social_graph_edgetypeassociation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('direct', self.gf('django.db.models.fields.related.ForeignKey')(related_name='is_direct_in', unique=True, to=orm['social_graph.EdgeType'])),
            ('inverse', self.gf('django.db.models.fields.related.ForeignKey')(related_name='is_inverse_in', unique=True, to=orm['social_graph.EdgeType'])),
        ))
        db.send_create_signal(u'social_graph', ['EdgeTypeAssociation'])

        # Adding model 'Edge'
        db.create_table(u'social_graph_edge', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fromNode_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_node_type_set_for_edge', to=orm['contenttypes.ContentType'])),
            ('fromNode_pk', self.gf('django.db.models.fields.TextField')()),
            ('toNode_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_node_type_set_for_edge', to=orm['contenttypes.ContentType'])),
            ('toNode_pk', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['social_graph.EdgeType'])),
            ('attributes', self.gf('social_graph.fields.JSONField')(default='{}')),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='edges', to=orm['sites.Site'])),
            ('auto', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'social_graph', ['Edge'])

        # Adding model 'EdgeCount'
        db.create_table(u'social_graph_edgecount', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fromNode_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('fromNode_pk', self.gf('django.db.models.fields.TextField')()),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['social_graph.EdgeType'])),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'social_graph', ['EdgeCount'])


    def backwards(self, orm):
        # Deleting model 'EdgeType'
        db.delete_table(u'social_graph_edgetype')

        # Deleting model 'EdgeTypeAssociation'
        db.delete_table(u'social_graph_edgetypeassociation')

        # Deleting model 'Edge'
        db.delete_table(u'social_graph_edge')

        # Deleting model 'EdgeCount'
        db.delete_table(u'social_graph_edgecount')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'social_graph.edge': {
            'Meta': {'ordering': "['-time']", 'object_name': 'Edge'},
            'attributes': ('social_graph.fields.JSONField', [], {'default': "'{}'"}),
            'auto': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fromNode_pk': ('django.db.models.fields.TextField', [], {}),
            'fromNode_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_node_type_set_for_edge'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'edges'", 'to': u"orm['sites.Site']"}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'toNode_pk': ('django.db.models.fields.TextField', [], {}),
            'toNode_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_node_type_set_for_edge'", 'to': u"orm['contenttypes.ContentType']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social_graph.EdgeType']"})
        },
        u'social_graph.edgecount': {
            'Meta': {'object_name': 'EdgeCount'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'fromNode_pk': ('django.db.models.fields.TextField', [], {}),
            'fromNode_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social_graph.EdgeType']"})
        },
        u'social_graph.edgetype': {
            'Meta': {'ordering': "['name']", 'object_name': 'EdgeType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'read_as': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'social_graph.edgetypeassociation': {
            'Meta': {'object_name': 'EdgeTypeAssociation'},
            'direct': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'is_direct_in'", 'unique': 'True', 'to': u"orm['social_graph.EdgeType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inverse': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'is_inverse_in'", 'unique': 'True', 'to': u"orm['social_graph.EdgeType']"})
        }
    }

    complete_apps = ['social_graph']
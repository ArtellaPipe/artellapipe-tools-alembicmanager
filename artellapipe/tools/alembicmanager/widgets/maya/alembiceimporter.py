#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Alembic Importer implementation for Houdini
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json
import logging

import tpDcc as tp

import artellapipe.register
from artellapipe.tools.alembicmanager.widgets.base import alembicimporter

if tp.is_maya():
    from tpDcc.dccs.maya.core import scene as maya_scene

LOGGER = logging.getLogger()


class MayaAlembicImporter(alembicimporter.AlembicImporter, object):
    def __init__(self, project, parent=None):
        super(MayaAlembicImporter, self).__init__(project=project, parent=parent)

    @classmethod
    def import_alembic(cls, project, alembic_path, parent=None, fix_path=False):
        """
        Implements  AlembicImporter import_alembic function
        Imports Alembic in current DCC scene
        :param project: ArtellaProject
        :param alembic_path: str
        :param parent: object
        :param fix_path: bool
        :return: bool
        """

        if not alembic_path or not os.path.isfile(alembic_path):
            LOGGER.warning('Alembic file {} does not exits!'.format(alembic_path))
            return None

        tag_json_file = os.path.join(
            os.path.dirname(alembic_path), os.path.basename(alembic_path).replace('.abc', '_abc.info'))
        valid_tag_info = True
        if os.path.isfile(tag_json_file):
            with open(tag_json_file, 'r') as f:
                tag_info = json.loads(f.read())
            if not tag_info:
                LOGGER.warning('No Alembic Info loaded!')
                valid_tag_info = False
        else:
            LOGGER.warning(
                'No Alembic Info file found! '
                'Take into account that imported Alembic is not supported by our current pipeline!')
            valid_tag_info = False

        if not parent:
            parent = tp.Dcc.create_empty_group(name=os.path.basename(alembic_path))
        else:
            if not tp.Dcc.object_exists(parent):
                parent = tp.Dcc.create_empty_group(name=parent)
            else:
                LOGGER.warning(
                    'Impossible to import Alembic into scene because'
                    ' node named "{}" already exists in the scene!'.format(parent))
                return

        if parent and valid_tag_info:
            cls._add_tag_info_data(project=project, tag_info=tag_info, attr_node=parent)

        track_nodes = maya_scene.TrackNodes()
        track_nodes.load()
        valid_import = alembic.import_alembic(
            project, alembic_path, mode='import', nodes=None, parent=parent, fix_path=fix_path)

        if not valid_import:
            return
        res = track_nodes.get_delta()

        # maya.cmds.viewFit(res, animate=True)

        return res

    @staticmethod
    def reference_alembic(project, alembic_path, namespace=None, fix_path=False):
        """
        References alembic file in current DCC scene
        :param project: ArtellaProject
        :param alembic_path: str
        :param namespace: str
        :param fix_path: bool
        """

        res = alembicimporter.AlembicImporter.reference_alembic(
            project=project, alembic_path=alembic_path, namespace=namespace, fix_path=fix_path)

        # maya.cmds.viewFit(res, animate=True)

        return res

    def _on_import_alembic(self, as_reference=False):
        """
        Overrides base AlembicImporter _on_import_alembic function
        Internal callback function that is called when Import/Reference Alembic button is clicked
        :param as_reference: bool
        """

        reference_nodes = super(MayaAlembicImporter, self)._on_import_alembic(as_reference=as_reference)

        if self._auto_smooth_display.isChecked():
            if reference_nodes and type(reference_nodes) in [list, tuple]:
                for obj in reference_nodes:
                    if obj and tp.Dcc.object_exists(obj):
                        if tp.Dcc.node_type(obj) == 'shape':
                            if tp.Dcc.attribute_exists(node=obj, attribute_name='aiSubdivType'):
                                tp.Dcc.set_integer_attribute_value(node=obj, attribute_name='aiSubdivType',
                                                                   attribute_value=1)
                        elif tp.Dcc.node_type(obj) == 'transform':
                            shapes = tp.Dcc.list_shapes(node=obj, full_path=True)
                            if not shapes:
                                continue
                            for s in shapes:
                                if tp.Dcc.attribute_exists(node=s, attribute_name='aiSubdivType'):
                                    tp.Dcc.set_integer_attribute_value(node=s, attribute_name='aiSubdivType',
                                                                       attribute_value=1)


artellapipe.register.register_class('AlembicImporter', MayaAlembicImporter)

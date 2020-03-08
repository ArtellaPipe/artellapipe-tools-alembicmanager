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

if tp.is_houdini():
    import hou

LOGGER = logging.getLogger()


class HoudiniAlembicImporter(alembicimporter.AlembicImporter, object):
    def __init__(self, project, parent=None):
        super(HoudiniAlembicImporter, self).__init__(project=project, parent=parent)

    def ui(self):
        super(HoudiniAlembicImporter, self).ui()

        self._auto_smooth_display.setChecked(False)
        self._auto_display_lbl.setEnabled(False)
        self._auto_smooth_display.setEnabled(False)

    @classmethod
    def import_alembic(cls, project, alembic_path, parent=None, fix_path=False):
        """
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
                'No Alembic Info file found! Take into account that imported Alembic '
                'is not supported by our current pipeline!')
            valid_tag_info = False

        n = hou.node('obj')
        node_name = os.path.basename(alembic_path)
        # parent = n.createNode('alembicarchive')
        geo = n.createNode('geo', node_name=node_name)
        parent = geo.createNode('alembic', node_name=node_name)

        if parent and valid_tag_info:
            cls._add_tag_info_data(project=project, tag_info=tag_info, attr_node=parent)

        res = alembic.import_alembic(
            project, alembic_path, mode='import', nodes=None, parent=parent, fix_path=fix_path)

        return res

    @staticmethod
    def reference_alembic(project, alembic_path, namespace=None, fix_path=False):
        """
        Overrides base AlembicImporter reference_alembic function
        References alembic file in current DCC scene
        :param project: ArtellaProject
        :param alembic_path: str
        :param namespace: str
        :param fix_path: bool
        """

        LOGGER.warning('Alembic Reference is not supported in Houdini!')
        return

    @staticmethod
    def _add_tag_info_data(project, tag_info, attr_node):
        """
        Overrides base AlembicImporter _add_tag_info_data function
        Internal function that updates the tag info of the Alembic node
        :param project: dict
        :param tag_info: dict
        :param attr_node: str
        """

        parm_group = attr_node.parmTemplateGroup()
        parm_folder = hou.FolderParmTemplate('folder', '{} Info'.format(project.name.title()))
        parm_folder.addParmTemplate(hou.StringParmTemplate('tag_info', 'Tag Info', 1))
        parm_group.append(parm_folder)
        attr_node.setParmTemplateGroup(parm_group)
        attr_node.parm('tag_info').set(str(tag_info))

    def _create_alembic_group(self, group_name):
        """
        Overrides base AlembicImporter _create_alembic_group function
        Internal function that creates root gruop for Alembic Node
        :return: str
        """

        n = hou.node('obj')
        if self._hou_archive_abc_node_cbx.isChecked():
            root = n.createNode('alembicarchive', node_name=group_name)
        else:
            geo = n.createNode('geo', node_name=group_name)
            root = geo.createNode('alembic', node_name=group_name)

        return root

    def _import_alembic(self, alembic_file, valid_tag_info, nodes=None, parent=None):
        """
        Overrides base AlembicImporter _import_alembic function
        Internal callback function that imports given alembic file
        :param alembic_file: str
        :param valid_tag_info: bool
        :param nodes: list
        :param parent: object
        :return:
        """

        if valid_tag_info:
            res = alembic.import_alembic(
                project=self._project, alembic_file=alembic_file, mode='import', nodes=nodes, parent=parent)
        else:
            res = alembic.import_alembic(
                project=self._project, alembic_file=alembic_file, mode='import', parent=parent)

        return res

    def _reference_alembic(self, alembic_file, namespace):
        """
        Overrides base AlembicImporter _reference_alembic function
        Internal function that references given alembic file
        :param alembic_file: str
        :param namespace: str
        :return:
        """

        LOGGER.warning('Alembic Reference is not supported in Houdini!')
        return


artellapipe.register.register_class('AlembicImporter', HoudiniAlembicImporter)

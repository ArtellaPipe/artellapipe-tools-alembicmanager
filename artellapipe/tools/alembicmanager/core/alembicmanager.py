#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export and import Alembic cache files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import artellapipe

# Defines ID of the tool
TOOL_ID = 'artellapipe-tools-alembicmanager'

# We skip the reloading of this module when launching the tool
no_reload = True


class AlembicManagerTool(artellapipe.Tool, object):
    def __init__(self, *args, **kwargs):
        super(AlembicManagerTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = artellapipe.Tool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Alembic Manager',
            'id': 'artellapipe-tools-alembicmanager',
            'logo': 'alembicmanager_logo',
            'icon': 'alembic',
            'tooltip': 'Tool used to export/import Alembics',
            'tags': ['alembic', 'import', 'export'],
            'sentry_id': 'https://e3795e7ffa23492e918f83ea3c4d658c@sentry.io/1764704',
            'import_order': ['widgets', 'core'],
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {'label': 'Alembic Manager', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [
                {'label': 'General',
                 'type': 'menu', 'children': [{'id': 'artellapipe-tools-alembicmanager', 'type': 'tool'}]}],
            'shelf': [
                {'name': 'General',
                 'children': [{'id': 'artellapipe-tools-alembicmanager', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config


class AlembicManagerToolset(artellapipe.Toolset, object):
    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(AlembicManagerToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from artellapipe.tools.alembicmanager.widgets import alembicmanager

        alembic_manager = alembicmanager.AlembicManager(
            project=self._project, config=self._config, settings=self._settings, parent=self)
        return [alembic_manager]

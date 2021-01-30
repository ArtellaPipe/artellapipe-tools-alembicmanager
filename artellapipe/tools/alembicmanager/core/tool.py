#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export and import Alembic cache files
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import argparse

from artellapipe.core import tool

from artellapipe.tools.alembicmanager.core import consts, toolset


class AlembicManagerTool(tool.ArtellaTool, object):

    ID = consts.TOOL_ID
    TOOLSET_CLASS = toolset.AlembicManagerToolset

    def __init__(self, *args, **kwargs):
        super(AlembicManagerTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = tool.ArtellaTool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Alembic Manager',
            'id': cls.ID,
            'logo': 'alembicmanager_logo',
            'icon': 'alembic',
            'tooltip': 'Tool used to export/import Alembics',
            'tags': ['alembic', 'import', 'export'],
            'sentry_id': 'https://e3795e7ffa23492e918f83ea3c4d658c@sentry.io/1764704',
            'import_order': ['widgets', 'core'],
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {'label': 'Alembic Manager', 'load_on_startup': False, 'color': '', 'background_color': ''}
        }
        base_tool_config.update(tool_config)

        return base_tool_config


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Launch {} tool'.format(consts.TOOL_ID))
    parser.add_argument('--project', required=True, help='Name of the artella project we want to launch the tool for')
    parser.add_argument(
        '--dev', required=False, default=True, help='Whether or not execute the tool in development mode')
    args = parser.parse_args()

    import tpDcc.loader
    from artellapipe.managers import tools

    tool_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    if tool_path not in sys.path:
        sys.path.append(tool_path)

    tpDcc.loader.init(dev=args.dev)
    tools.run_tool(AlembicManagerTool.ID, project_name=args.project, dev=args.dev)

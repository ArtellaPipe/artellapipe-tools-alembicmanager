#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export and import Alembic cache files
"""

from __future__ import print_function, division, absolute_import

from artellapipe.core import tool


class AlembicManagerToolset(tool.ArtellaToolset, object):
    def __init__(self, *args, **kwargs):
        super(AlembicManagerToolset, self).__init__(*args, **kwargs)

    def contents(self):

        from artellapipe.tools.alembicmanager.core import view

        alembic_manager_view = view.AlembicManagerView(
            project=self._project, config=self._config, settings=self._settings, parent=self)
        return [alembic_manager_view]

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tool to export/import Alembic (.abc) files
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import logging.config
from functools import partial

from Qt.QtWidgets import *

import tpDcc
from tpDcc.libs.qt.widgets import stack, splitters

import artellapipe
import artellapipe.tools.alembicmanager

LOGGER = logging.getLogger()


class AlembicManager(artellapipe.ToolWidget, object):

    def __init__(self, project, config, settings, parent):
        super(AlembicManager, self).__init__(project=project, config=config, settings=settings, parent=parent)

    def ui(self):
        super(AlembicManager, self).ui()

        export_icon = tpDcc.ResourcesMgr().icon('export')
        import_icon = tpDcc.ResourcesMgr().icon('import')

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(2, 2, 2, 2)
        buttons_layout.setSpacing(2)
        self.main_layout.addLayout(buttons_layout)
        self.main_layout.addLayout(splitters.SplitterLayout())

        self._exporter_btn = QPushButton('Exporter')
        self._exporter_btn.setIcon(export_icon)
        self._exporter_btn.setMinimumWidth(80)
        self._exporter_btn.setCheckable(True)
        self._importer_btn = QPushButton('Importer')
        self._importer_btn.setIcon(import_icon)
        self._importer_btn.setMinimumWidth(80)
        self._importer_btn.setCheckable(True)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        buttons_layout.addWidget(self._exporter_btn)
        buttons_layout.addWidget(self._importer_btn)
        buttons_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self._buttons_grp = QButtonGroup(self)
        self._buttons_grp.setExclusive(True)
        self._buttons_grp.addButton(self._exporter_btn)
        self._buttons_grp.addButton(self._importer_btn)
        self._exporter_btn.setChecked(True)

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        self._alembic_exporter = artellapipe.AlembicExporter(project=self.project)
        self._alembic_importer = artellapipe.AlembicImporter(project=self.project)

        self._stack.addWidget(self._alembic_exporter)
        self._stack.addWidget(self._alembic_importer)

    def setup_signals(self):
        self._stack.animFinished.connect(self._on_stack_anim_finished)
        self._exporter_btn.clicked.connect(partial(self._on_slide_stack, 0))
        self._importer_btn.clicked.connect(partial(self._on_slide_stack, 1))
        self._alembic_exporter.showWarning.connect(self._on_show_warning)
        self._alembic_exporter.showOk.connect(self._on_show_ok)
        self._alembic_importer.showOk.connect(self._on_show_ok)

    def _on_slide_stack(self, index):
        """
        Internal callback function that is called when stack needs to change current widget
        :param index: int
        """

        if index == self._stack.currentIndex():
            return

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(False)

        self._stack.slide_in_index(index)

    def _on_stack_anim_finished(self):
        """
        Internal callback function that is called when stack anim finish
        """

        for btn in self._buttons_grp.buttons():
            btn.setEnabled(True)

        if self._stack.currentWidget() == self._alembic_exporter:
            self._alembic_exporter.refresh()

    def _on_show_ok(self, warning_msg):
        """
        Internal callback function that is called when an ok message should be showed
        :param warning_msg: str
        """

        LOGGER.debug(warning_msg)
        self.show_ok_message(warning_msg)

    def _on_show_warning(self, warning_msg):
        """
        Internal callback function that is called when a warning message should be showed
        :param warning_msg: str
        """

        LOGGER.warning(warning_msg)
        self.show_warning_message(warning_msg)

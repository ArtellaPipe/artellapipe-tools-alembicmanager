#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Alembic Exporter
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import json
import logging

from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QSizePolicy, QWidget

from tpDcc import dcc
from tpDcc.managers import resources
from tpDcc.libs.python import decorators, folder as folder_utils, path as path_utils
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, label, lineedit, dividers, stack, spinbox, buttons, checkbox

from artellapipe.libs.artella.core import artellalib
from artellapipe.libs.alembic.core import alembic
from artellapipe.widgets import waiter, spinner

from artellapipe.tools.alembicmanager.core import consts

logger = logging.getLogger(consts.TOOL_ID)


class _MetaAlembicExporter(type):
    def __call__(self, *args, **kwargs):
        return type.__call__(BaseAlembicExporter, *args, **kwargs)


class BaseAlembicExporter(base.BaseWidget, object):

    showOk = Signal(str)
    showWarning = Signal(str)

    def __init__(self, project, parent=None):

        self._project = project

        super(BaseAlembicExporter, self).__init__(parent=parent)

    def ui(self):
        super(BaseAlembicExporter, self).ui()

        self._stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self._stack)

        exporter_widget = QWidget()
        exporter_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        exporter_widget.setLayout(exporter_layout)
        self._stack.addWidget(exporter_widget)

        self._waiter = waiter.ArtellaWaiter(spinner_type=spinner.SpinnerType.Thumb)
        self._stack.addWidget(self._waiter)

        buttons_layout = layouts.GridLayout()
        exporter_layout.addLayout(buttons_layout)

        name_lbl = label.BaseLabel('Alembic Name: ', parent=self)
        self._name_line = lineedit.BaseLineEdit(parent=self)
        buttons_layout.addWidget(name_lbl, 0, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._name_line, 0, 1)

        shot_name_lbl = label.BaseLabel('Shot Name: ', parent=self)
        self._shot_line = lineedit.BaseLineEdit(parent=self)
        buttons_layout.addWidget(shot_name_lbl, 1, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(self._shot_line, 1, 1)

        frame_range_lbl = label.BaseLabel('Frame Range: ', parent=self)
        self._start = spinbox.BaseSpinBox(parent=self)
        self._start.setRange(-sys.maxint, sys.maxint)
        self._start.setFixedHeight(20)
        self._start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._end = spinbox.BaseSpinBox(parent=self)
        self._end.setRange(-sys.maxint, sys.maxint)
        self._end.setFixedHeight(20)
        self._end.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame_range_widget = QWidget()
        frame_range_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        frame_range_widget.setLayout(frame_range_layout)
        for widget in [frame_range_lbl, self._start, self._end]:
            frame_range_layout.addWidget(widget)
        buttons_layout.addWidget(frame_range_lbl, 2, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(frame_range_widget, 2, 1)

        folder_icon = resources.icon('folder')
        export_path_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        export_path_widget = QWidget()
        export_path_widget.setLayout(export_path_layout)
        export_path_lbl = label.BaseLabel('Export Path: ', parent=self)
        self._export_path_line = lineedit.BaseLineEdit(parent=self)
        self._export_path_line.setReadOnly(True)
        self._export_path_line.setText(self._project.get_path())
        self._export_path_btn = buttons.BaseButton(parent=self)
        self._export_path_btn.setIcon(folder_icon)
        self._export_path_btn.setIconSize(QSize(18, 18))
        self._export_path_btn.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0); border: 0px solid rgba(255,255,255,0);")
        export_path_layout.addWidget(self._export_path_line)
        export_path_layout.addWidget(self._export_path_btn)
        buttons_layout.addWidget(export_path_lbl, 3, 0, 1, 1, Qt.AlignRight)
        buttons_layout.addWidget(export_path_widget, 3, 1)

        exporter_layout.addLayout(dividers.DividerLayout())

        checkboxes_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        exporter_layout.addLayout(checkboxes_layout)

        self._open_folder_after_export_cbx = checkbox.BaseCheckBox('Open Folder After Export?', parent=self)
        self._open_folder_after_export_cbx.setChecked(True)
        checkboxes_layout.addWidget(self._open_folder_after_export_cbx)
        self._export_all_alembics_together_cbx = checkbox.BaseCheckBox(
            'Export All Selected Geometry in One Alembic?', parent=self)
        self._export_all_alembics_together_cbx.setChecked(True)
        checkboxes_layout.addWidget(self._export_all_alembics_together_cbx)

        exporter_layout.addLayout(dividers.DividerLayout())

        self._export_btn = buttons.BaseButton('Export', parent=self)
        self._export_btn.setIcon(resources.icon('export'))
        self._export_btn.setEnabled(False)
        self.main_layout.addWidget(self._export_btn)

        exporter_layout.addStretch()

        self.refresh()

    def setup_signals(self):
        self._name_line.textChanged.connect(self.refresh)
        self._export_path_btn.clicked.connect(self._on_set_export_path)
        self._export_btn.clicked.connect(self._on_export)
        self._stack.animFinished.connect(self._on_stack_anim_finished)

    def refresh(self):
        """
        Function that update necessary info of the tool
        """

        self._refresh_frame_ranges()
        self._refresh_shot_name()
        self._refresh_alembic_name()
        self._refresh_export_button_state()

    def get_selected_alembic_group(self):
        """
        Returns the name of the currently selected set
        :return: str
        """

        alembic_group_name = self._alembic_groups_combo.currentText()
        return alembic_group_name

    def export_alembic(self, export_path, object_to_export=None, start_frame=1, end_frame=1):
        """
        Function that exports alembic in the given path
        :param export_path: str, path to export alembic into
        :param object_to_export: str, object to export (optional)
        :param start_frame: int, start frame when exporting animated Alembic caches
        :param end_frame: int, end frame when exporting animated Alembic caches
        """

        if not object_to_export or not dcc.client().node_exists(object_to_export):
            object_to_export = dcc.client().selected_nodes(False)
            if not object_to_export:
                self.show_warning.emit(
                    'Impossible to export Alembic from non-existent object {}'.format(object_to_export))
                return
            object_to_export = object_to_export[0]

        dcc.client().select_node(object_to_export)
        self.refresh()

        self._alembic_groups_combo.setCurrentIndex(1)
        self._export_path_line.setText(export_path)
        self._start.setValue(start_frame)
        self._end.setValue(end_frame)
        self._on_export()

        dcc.client().new_file()

    def _refresh_alembic_name(self):
        """
        Internal function that updates Alembic name
        """

        if self._name_line.text() != '':
            return

        sel = dcc.client().selected_nodes()
        if sel:
            sel = sel[0]
            is_referenced = dcc.client().node_is_referenced(sel)
            if is_referenced:
                sel_namespace = dcc.client().node_namespace(sel)
                if not sel_namespace or not sel_namespace.startswith(':'):
                    pass
                else:
                    sel_namespace = sel_namespace[1:] + ':'
                    sel = sel.replace(sel_namespace, '')

            self._name_line.setText(dcc.client().node_short_name(sel))

    def _refresh_frame_ranges(self):
        """
        Internal function that updates the frame ranges values
        """

        frame_range = dcc.client().get_time_slider_range()
        self._start.setValue(int(frame_range[0]))
        self._end.setValue(int(frame_range[1]))

    def _refresh_shot_name(self):
        """
        Internal function that updates the shot name QLineEdit text
        """

        shot_name = ''
        current_scene = dcc.client().scene_name()
        if current_scene:
            current_scene = os.path.basename(current_scene)

        # shot_regex = artellapipe.ShotsMgr().get_shot_regex()
        # m = shot_regex.match(current_scene)
        # if m:
        #     shot_name = m.group(1)

        self._shot_line.setText(shot_name)

    def _refresh_export_button_state(self):
        """
        Internal function that updates the status of the export button
        """

        enabled = bool(self._name_line.text() and self._export_path_line.text())
        self._export_btn.setEnabled(enabled)

    def _add_tag_attributes(self, attr_node, tag_node):
        # We add attributes to the first node in the list
        attrs = dcc.client().list_user_attributes(tag_node)
        tag_info = dict()
        for attr in attrs:
            try:
                tag_info[attr] = str(dcc.client().get_attribute_value(node=tag_info, attribute_name=attr))
            except Exception:
                pass
        if not tag_info:
            logger.warning('Node has not valid tag data: {}'.format(tag_node))
            return

        if not dcc.client().attribute_exists(node=attr_node, attribute_name='tag_info'):
            dcc.client().add_string_attribute(node=attr_node, attribute_name='tag_info', keyable=True)
        dcc.client().set_string_attribute_value(node=attr_node, attribute_name='tag_info', attribute_value=str(tag_info))

    def _get_tag_atributes_dict(self, tag_node):
        # We add attributes to the first node in the list
        tag_info = dict()
        if not tag_node:
            return tag_info

        attrs = dcc.client().list_user_attributes(tag_node)
        for attr in attrs:
            try:
                tag_info[attr] = dcc.client().get_attribute_value(node=tag_node, attribute_name=attr)
            except Exception:
                pass
        if not tag_info:
            logger.warning('Node has not valid tag data: {}'.format(tag_node))
            return

        return tag_info

    def _get_alembic_rig_export_list(self, root_node):
        export_list = list()
        # root_node_child_count = root_node.childCount()
        # if root_node_child_count > 0 or len(dcc.client().list_shapes(root_node.name)) > 0:
        #     for j in range(root_node.childCount()):
        #         c = root_node.child(j)
        #         c_name = c.name
        #         if type(c_name) in [list, tuple]:
        #             c_name = c_name[0]
        #         if isinstance(c, AlembicExporterModelHires):
        #             children = dcc.client().node_children(node=c_name, all_hierarchy=True, full_path=True)
        #             export_list.extend(children)
        #             export_list.append(c_name)
        #
        #             # if tag_node:
        #             #     self._add_tag_attributes(c_name, tag_node)
        #             # export_list.append(c_name)
        #         else:
        #             if 'transform' != dcc.client().node_type(c_name):
        #                 xform = dcc.client().node_parent(node=c_name, full_path=True)
        #                 parent_xform = dcc.client().node_parent(node=xform, full_path=True)
        #                 if parent_xform:
        #                     children = dcc.client().node_children(node=parent_xform, all_hierarchy=True, full_path=True)
        #                     export_list.extend(children)
        #             else:
        #                 children = dcc.client().node_children(node=c_name, all_hierarchy=True, full_path=True)
        #                 export_list.extend(children)
        #
        # for obj in reversed(export_list):
        #     if dcc.client().node_type(obj) != 'transform':
        #         export_list.remove(obj)
        #         continue
        #     is_visible = dcc.client().get_attribute_value(node=obj, attribute_name='visibility')
        #     if not is_visible:
        #         export_list.remove(obj)
        #         continue
        #     if dcc.client().attribute_exists(node=obj, attribute_name='displaySmoothMesh'):
        #         dcc.client().set_integer_attribute_value(node=obj, attribute_name='displaySmoothMesh', attribute_value=2)
        #
        # childs_to_remove = list()
        # for obj in export_list:
        #     children = dcc.client().node_children(node=obj, all_hierarchy=True, full_path=True)
        #     shapes = dcc.client().list_children_shapes(node=obj, all_hierarchy=True, full_path=True)
        #     if children and not shapes:
        #         childs_to_remove.extend(children)
        #
        # if childs_to_remove:
        #     for obj in childs_to_remove:
        #         if obj in export_list:
        #             export_list.remove(obj)
        #
        # return export_list

    def _export(self):
        """
        Internal function that exports Alembic
        """

        out_folder = self._export_path_line.text()
        if not os.path.exists(out_folder):
            dcc.client().confirm_dialog(
                title='Error during Alembic Exportation',
                message='Output Path does not exists: {}. Select a valid one!'.format(out_folder)
            )
            return

        nodes_to_export = dcc.client().selected_nodes()
        if not nodes_to_export:
            logger.error('No nodes to export as Alembic!')
            return False

        for n in nodes_to_export:
            if not dcc.node_exists(n):
                logger.error('Node "{}" does not exists in current scene!'.format(n))
                return False

        root_nodes = list()
        for n in nodes_to_export:
            root_node = dcc.client().node_root(node=n)
            if root_node not in root_nodes:
                root_nodes.append(root_node)

        if not root_nodes:
            logger.error('Not nodes to export as Alembic!')
            return False

        file_paths = list()

        export_info = list()
        if self._export_all_alembics_together_cbx.isChecked():
            export_path = path_utils.clean_path(out_folder + dcc.client().node_short_name(root_nodes[0]) + '.abc')
            file_paths.append(export_path)
            export_info.append({'path': export_path, 'nodes': root_nodes})
        else:
            for n in root_nodes:
                export_path = path_utils.clean_path(out_folder + dcc.client().node_short_name(n) + '.abc')
                file_paths.append(export_path)
                export_info.append({'path': export_path, 'nodes': [n]})

        res = dcc.client().confirm_dialog(
            title='Export Alembic File',
            message='Are you sure you want to export Alembic to files?\n\n' + '\n'.join([p for p in file_paths]),
            button=['Yes', 'No'],
            default_button='Yes',
            cancel_button='No',
            dismiss_string='No'
        )
        if res != 'Yes':
            logger.debug('Aborting Alembic Export operation ...')
            return

        result = True
        try:
            self._export_alembics(export_info)
        except Exception as exc:
            logger.error('Something went wrong during Alembic export process: {}'.format(exc))
            result = False

        self._stack.slide_in_index(0)

        return result

    def _export_alembics(self, export_info):

        def _recursive_hierarchy(transform):
            child_nodes = list()
            if not transform:
                return child_nodes
            transforms = dcc.client().list_relatives(node=transform, full_path=True)
            if not transforms:
                return child_nodes
            for eachTransform in transforms:
                if dcc.client().node_type(eachTransform) == 'transform':
                    child_nodes.append(eachTransform)
                    child_nodes.extend(_recursive_hierarchy(eachTransform))
            return child_nodes

        for info in export_info:
            export_path = info.get('path')
            abc_nodes = info.get('nodes')

            if os.path.isfile(export_path):
                res = dcc.client().confirm_dialog(
                    title='Alembic File already exits!',
                    message='Are you sure you want to overwrite already existing Alembic File?\n\n{}'.format(
                        export_path),
                    button=['Yes', 'No'],
                    default_button='Yes',
                    cancel_button='No',
                    dismiss_string='No'
                )
                if res != 'Yes':
                    logger.debug('Aborting Alembic Export operation ...')
                    return

            tag_info = dict()

            geo_shapes = list()
            for node in abc_nodes:
                node_shapes = dcc.client().list_shapes(node=node) or list()
                for shape in node_shapes:
                    if dcc.client().check_object_type(shape, 'shape', check_sub_types=True):
                        geo_shapes.append(node)
                children_nodes = dcc.client().list_children(node, all_hierarchy=True, full_path=True)
                for child_node in children_nodes:
                    node_shapes = dcc.client().list_shapes(node=child_node) or list()
                    for shape in node_shapes:
                        if dcc.client().check_object_type(shape, 'shape', check_sub_types=True):
                            geo_shapes.append(child_node)
                        if dcc.client().attribute_exists(node=child_node, attribute_name='displaySmoothMesh'):
                            dcc.client().set_integer_attribute_value(node=child_node, attribute_name='displaySmoothMesh',
                                                               attribute_value=2)

                root_tag = artellapipe.TagsMgr().get_tag_data_node_from_current_selection(node)
                root_tag_info = self._get_tag_atributes_dict(root_tag)
                if root_tag_info:
                    tag_info[node] = root_tag_info

                if not geo_shapes:
                    self.showWarning.emit('No geometry data to export! Aborting Alembic Export operation ...')
                    return
                geo_shape = geo_shapes[0]

                # Retrieve all Arnold attributes to export from the first element of the list
                arnold_attrs = [attr for attr in dcc.client().list_attributes(geo_shape) if attr.startswith('ai')]

                artellalib.lock_file(export_path, True)

                valid_alembic = alembic.export_alembic(
                    root=[node],
                    alembic_file=export_path,
                    frame_range=[[float(self._start.value()), float(self._end.value())]],
                    user_attr=arnold_attrs,
                    uv_write=True,
                    write_uv_sets=True,
                    write_creases=True
                )
                if not valid_alembic:
                    logger.warning('Error while exporting Alembic file: {}'.format(export_path))
                    return

                tag_json_file = export_path.replace('.abc', '_abc.info')
                with open(tag_json_file, 'w') as f:
                    json.dump(tag_info, f)

                if self._open_folder_after_export_cbx.isChecked():
                    folder_utils.open_folder(os.path.dirname(export_path))

                if dcc.client().attribute_exists(node=node, attribute_name='tag_info'):
                    try:
                        dcc.client().delete_attribute(node=node, attribute_name='tag_info')
                    except Exception as exc:
                        logger.warning('Impossible to clean tag_info node from "{}!'.format(node))

            self.showOk.emit(
                'Alembic File: {} exported successfully!'.format(os.path.basename(os.path.basename(export_path))))

    def _on_set_export_path(self):
        """
        Internal function that is called when the user selects the folder icon
        Allows the user to select a path to export Alembic group contents
        """

        res = dcc.client().select_file_dialog(title='Select Alembic Export Folder', start_directory=self._project.get_path())
        if not res:
            return

        self._export_path_line.setText(res)
        self.refresh()

    def _on_stack_anim_finished(self, index):
        """
        Internal callback function that is called when stack animation finishes
        :param index:
        :return:
        """

        if index == 1:
            self._export()

    def _on_export(self):
        """
        Internal callback function that is called when the user presses Export button
        """

        self._stack.slide_in_index(1)


@decorators.add_metaclass(_MetaAlembicExporter)
class AlembicExporter(object):
    pass

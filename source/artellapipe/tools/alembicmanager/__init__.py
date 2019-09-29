#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artellapipe-tools-lightrigsmanager
"""

import os
import sys
import inspect

import sentry_sdk
sentry_sdk.init("https://5382260e62d448b881a24ea95f70ef4f@sentry.io/1764569")

from tpPyUtils import importer

from artellapipe.utils import resource, exceptions


class AlembicManager(importer.Importer, object):
    def __init__(self):
        super(AlembicManager, self).__init__(module_name='artellapipe.tools.alembicmanager')

    def get_module_path(self):
        """
        Returns path where tpNameIt module is stored
        :return: str
        """

        try:
            mod_dir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)
        except Exception:
            try:
                mod_dir = os.path.dirname(__file__)
            except Exception:
                try:
                    import tpDccLib
                    mod_dir = tpDccLib.__path__[0]
                except Exception:
                    return None

        return mod_dir


def init(do_reload=False):
    """
    Initializes module
    """

    packages_order = [
        'artellapipe.tools.alembicmanager.widgets',
        'artellapipe.tools.alembicmanager.core'
    ]

    alembicmanager_importer = importer.init_importer(importer_class=AlembicManager, do_reload=False)
    alembicmanager_importer.import_packages(order=packages_order, only_packages=False)
    if do_reload:
        alembicmanager_importer.reload_all()

    create_logger_directory()

    resources_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
    resource.ResourceManager.instance().register_resource(resources_path)


@exceptions.sentry_exception
def run(project, do_reload=False):
    """
    Run ArtellaManager Tool
    :param project: ArtellaProject
    :param do_reload: bool
    :return: AssetsManager
    """

    init(do_reload=do_reload)
    from artellapipe.tools.alembicmanager.core import alembicmanager
    win = alembicmanager.run(project=project)
    return win


def create_logger_directory():
    """
    Creates artellapipe-gui logger directory
    """

    artellapipe_logger_dir = os.path.normpath(os.path.join(os.path.expanduser('~'), 'artellapipe', 'logs'))
    if not os.path.isdir(artellapipe_logger_dir):
        os.makedirs(artellapipe_logger_dir)


def get_logging_config():
    """
    Returns logging configuration file path
    :return: str
    """

    return os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))


def get_logging_level():
    """
    Returns logging level to use
    :return: str
    """

    if os.environ.get('ARTELLAPIPE_TOOLS_ALEMBICMANAGER_LOG_LEVEL', None):
        return os.environ.get('ARTELLAPIPE_TOOLS_ALEMBICMANAGER_LOG_LEVEL')

    return os.environ.get('ARTELLAPIPE_TOOLS_ALEMBICMANAGER_LOG_LEVEL', 'WARNING')


def register_importer(cls):
    """
    This function registers given class
    :param cls: class, Alembic importer class we want to register
    """

    sys.modules[__name__].__dict__['alembic_importer'] = cls


def register_exporter(cls):
    """
    This function registers given class
    :param cls: class, Alembic importer class we want to register
    """

    sys.modules[__name__].__dict__['alembic_exporter'] = cls

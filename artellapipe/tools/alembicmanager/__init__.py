#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for artellapipe-tools-alembicmanager
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import sys


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

#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains general tests for artellapipe-tools-alembicmanager
"""

import pytest

from artellapipe.tools.alembicmanager import __version__


def test_version():
    assert __version__.__version__

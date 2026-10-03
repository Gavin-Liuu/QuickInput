# -*- coding: utf-8 -*-
"""Pytest shared fixtures."""

import sys
import pytest
from PyQt5 import QtWidgets


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    return app

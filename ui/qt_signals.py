# -*- coding: utf-8 -*-
"""Qt Signals helper for thread-safe cross-thread UI updates."""

from PyQt5 import QtCore


class ExecutorSignals(QtCore.QObject):
    """Signals emitted by ActionExecutor to safely update Qt UI across threads."""
    started = QtCore.pyqtSignal(str, int)
    step_progress = QtCore.pyqtSignal(int, int, str)
    finished = QtCore.pyqtSignal(str, bool, str)


class TargetSignals(QtCore.QObject):
    """Signals emitted when target window changes."""
    target_changed = QtCore.pyqtSignal(dict)

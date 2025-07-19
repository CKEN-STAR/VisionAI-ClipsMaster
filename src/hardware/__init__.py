#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 硬件功能包
"""

from .compute_offloader import get_compute_offloader, offload_task

__all__ = ['get_compute_offloader', 'offload_task']

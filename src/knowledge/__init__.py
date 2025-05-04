#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识模块包

提供剧本知识图谱构建、分析和查询功能。
"""

from src.knowledge.graph_builder import KnowledgeGraph, build_knowledge_graph

__all__ = ['KnowledgeGraph', 'build_knowledge_graph']

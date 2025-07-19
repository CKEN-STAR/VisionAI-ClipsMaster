"""
时空折叠引擎

用于非线性叙事结构重构和时间轴重排序的模块
"""

from src.nonlinear.time_folder import (
    TimeFolder, fold_timeline, TimeFoldingStrategy,
    get_folding_strategy, list_folding_strategies
)

from src.nonlinear.pov_coordinator import (
    POVManager, TransitionType, manage_pov_transitions, get_transition_types
)

from src.nonlinear.suspense_planter import (
    SuspensePlanter, ClueType, plant_early_clues, plant_suspense, get_clue_types
)

from src.nonlinear.rhythm_tuner import (
    RhythmTuner, PaceType, adjust_pacing, get_available_structures
)

from src.nonlinear.meta_annotator import (
    MetaAnnotator, StructuralRole, LogicChainType, add_meta_comments,
    get_scene_structural_role, get_scene_connections, get_scene_logic_chain
)

__all__ = [
    'TimeFolder', 'fold_timeline', 'TimeFoldingStrategy',
    'get_folding_strategy', 'list_folding_strategies',
    'POVManager', 'TransitionType', 'manage_pov_transitions', 'get_transition_types',
    'SuspensePlanter', 'ClueType', 'plant_early_clues', 'plant_suspense', 'get_clue_types',
    'RhythmTuner', 'PaceType', 'adjust_pacing', 'get_available_structures',
    'MetaAnnotator', 'StructuralRole', 'LogicChainType', 'add_meta_comments',
    'get_scene_structural_role', 'get_scene_connections', 'get_scene_logic_chain'
] 
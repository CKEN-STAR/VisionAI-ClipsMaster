"""
VisionAI-ClipsMaster - Main Application

Creates mixed video clips by analyzing subtitles and stitching original footage by timestamps.
Includes a robust memory safety framework for limited memory environments (4GB without GPU).
"""

import os
import sys
import argparse
import logging
import time
from typing import Dict, Any, List, Optional

# Import memory safety framework components
from core.safe_executor import SafeExecutor, MemoryThresholdExceeded
from core.recovery_manager import RecoveryManager
from core.effect_validator import EffectValidator
from core.event_tracer import EventTracer
from knowledge_base.knowledge_base import KnowledgeBase
from knowledge_base.knowledge_service import KnowledgeService
from test_env.memory_config import MemoryConfig, MemoryScenario
from test_env.memory_simulator import MemorySimulator
from test_env.test_runner import TestRunner
from tests.memory_pressurer import MemoryPressurer, get_memory_pressurer

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VisionAI-ClipsMaster")


def init_memory_safety_framework(memory_limit_mb: Optional[int] = None) -> Dict[str, Any]:
    """
    Initialize the memory safety framework.
    
    Args:
        memory_limit_mb: Memory limit in MB, or None to use default
        
    Returns:
        Dictionary with framework components
    """
    # Set up memory configuration
    memory_config = MemoryConfig(
        scenario=MemoryScenario.BASELINE if memory_limit_mb is None else MemoryScenario.BASELINE,
        custom_limit_mb=memory_limit_mb
    )
    
    # Initialize components
    recovery_manager = RecoveryManager()
    effect_validator = EffectValidator()
    event_tracer = EventTracer()
    
    # Initialize safe executor
    safe_executor = SafeExecutor(
        memory_threshold_mb=memory_config.warning_threshold_mb,
        critical_threshold_mb=memory_config.critical_threshold_mb,
        recovery_manager=recovery_manager,
        effect_validator=effect_validator,
        event_tracer=event_tracer
    )
    
    # Initialize knowledge base components
    kb_dir = os.path.join("knowledge_base", "data")
    os.makedirs(kb_dir, exist_ok=True)
    
    patterns_file = os.path.join(kb_dir, "patterns.json")
    cases_file = os.path.join(kb_dir, "custom_cases.json")
    
    knowledge_base = KnowledgeBase(
        default_patterns_file=patterns_file if os.path.exists(patterns_file) else None,
        custom_cases_file=cases_file if os.path.exists(cases_file) else None
    )
    
    # If pattern file doesn't exist, save built-in patterns
    if not os.path.exists(patterns_file):
        knowledge_base.save_patterns(patterns_file)
    
    # If cases file doesn't exist, save empty cases file
    if not os.path.exists(cases_file):
        knowledge_base.save_custom_cases(cases_file)
    
    knowledge_service = KnowledgeService(
        knowledge_base=knowledge_base,
        event_tracer=event_tracer
    )
    
    logger.info("Memory safety framework initialized")
    
    return {
        "memory_config": memory_config,
        "safe_executor": safe_executor,
        "recovery_manager": recovery_manager,
        "effect_validator": effect_validator,
        "event_tracer": event_tracer,
        "knowledge_base": knowledge_base,
        "knowledge_service": knowledge_service
    }


def run_memory_tests() -> None:
    """Run memory safety tests."""
    logger.info("Running memory safety tests...")
    
    # Create test runner
    runner = TestRunner()
    
    # Run predefined test suite
    results = runner.run_predefined_test_suite()
    
    # Generate and print report
    report = runner.generate_report(results, "test_report.txt")
    print("\nTest Report Summary:")
    print("-------------------")
    
    # Print summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success)
    print(f"Total Tests: {total_tests}")
    print(f"Passed Tests: {passed_tests} ({passed_tests / total_tests * 100:.1f}%)")
    print(f"Failed Tests: {total_tests - passed_tests} ({(total_tests - passed_tests) / total_tests * 100:.1f}%)")
    print(f"See 'test_report.txt' for full details")


def simulate_memory_pressure(pattern: str, duration_sec: int = 30) -> None:
    """
    Simulate memory pressure with the specified pattern.
    
    Args:
        pattern: Memory pattern to simulate
        duration_sec: Duration of simulation in seconds
    """
    logger.info(f"Simulating memory pressure: {pattern} for {duration_sec} seconds")
    
    # Get memory pressurer instance
    pressurer = get_memory_pressurer()
    
    # Map input pattern to pressurer pattern
    if pattern == "steady_growth":
        pressurer_pattern = "stepped"
        kwargs = {
            "step_size_mb": 100.0,
            "step_interval_sec": 1.0,
            "duration_sec": duration_sec
        }
    elif pattern == "spikes":
        pressurer_pattern = "spike"
        kwargs = {
            "target_percent": 80.0,
            "hold_sec": 5.0
        }
        # For spike pattern, run multiple times to fill duration
        cycles = max(1, duration_sec // 10)
        print(f"Running {cycles} memory spike cycles...")
        for i in range(cycles):
            if i > 0:
                print(f"Running spike cycle {i+1}/{cycles}...")
            pressurer.generate_memory_spike(**kwargs)
            if i < cycles - 1:
                print("Waiting for system to stabilize...")
                time.sleep(5)
        return
    elif pattern == "leak":
        # Simulate memory leak using stepped growth without releasing
        pressurer_pattern = "stepped"
        kwargs = {
            "step_size_mb": 50.0,  # Smaller steps for smoother growth
            "step_interval_sec": 1.0,
            "duration_sec": duration_sec
        }
    elif pattern == "fragmentation" or pattern == "mixed":
        pressurer_pattern = "sawtooth"
        kwargs = {
            "max_mb": None,  # Use default (60% of system memory)
            "min_mb": 100.0,
            "period_sec": 10.0,
            "cycles": max(2, duration_sec // 10)
        }
    else:
        logger.error(f"Unknown memory pattern: {pattern}")
        return
    
    if pattern != "spikes":  # Spikes handled separately above
        # Run the pressure pattern
        pressurer.start_pressure_pattern(pressurer_pattern, **kwargs)
        
        # Wait for the specified duration if not already included in the pattern
        if "duration_sec" not in kwargs:
            print(f"Pressure pattern running. Press Ctrl+C to stop early...")
            try:
                time.sleep(duration_sec)
            except KeyboardInterrupt:
                print("\nStopping memory pressure simulation early...")
            finally:
                # Stop the pressure
                pressurer.stop_pressure()


def run_knowledge_base_cli() -> None:
    """Run the knowledge base CLI."""
    from knowledge_base.kb_cli import main as kb_main

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

    kb_main()


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="VisionAI-ClipsMaster - Video processing with memory safety framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--memory-limit", type=int, help="Memory limit in MB")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add test command
    test_parser = subparsers.add_parser("test", help="Run memory safety tests")
    
    # Add simulate command
    simulate_parser = subparsers.add_parser("simulate", help="Simulate memory pressure")
    simulate_parser.add_argument(
        "pattern", 
        choices=["steady_growth", "spikes", "leak", "fragmentation", "mixed", "stepped", "spike", "sawtooth"],
        help="Memory pattern to simulate"
    )
    simulate_parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    
    # Add advanced simulation parameters
    simulate_parser.add_argument("--step-size", type=float, help="Step size in MB for stepped pattern")
    simulate_parser.add_argument("--target-percent", type=float, help="Target percentage for spike pattern")
    simulate_parser.add_argument("--hold-time", type=float, help="Hold time in seconds for spike pattern")
    simulate_parser.add_argument("--min-mb", type=float, help="Minimum memory in MB for sawtooth pattern")
    simulate_parser.add_argument("--max-mb", type=float, help="Maximum memory in MB for sawtooth pattern")
    simulate_parser.add_argument("--period", type=float, help="Period in seconds for sawtooth pattern")
    simulate_parser.add_argument("--cycles", type=int, help="Number of cycles for sawtooth pattern")
    
    # Add knowledge base CLI command
    kb_parser = subparsers.add_parser("kb", help="Run knowledge base CLI")
    
    args = parser.parse_args()
    
    # Initialize memory safety framework
    framework = init_memory_safety_framework(args.memory_limit)
    
    if args.command == "test":
        run_memory_tests()
    elif args.command == "simulate":
        # Check if pattern is one of the new direct patterns
        if args.pattern in ["stepped", "spike", "sawtooth"]:
            pressurer = get_memory_pressurer()
            kwargs = {}
            
            # Add common parameters
            if args.duration:
                kwargs["duration_sec"] = args.duration
                
            # Add pattern-specific parameters
            if args.pattern == "stepped":
                if args.step_size:
                    kwargs["step_size_mb"] = args.step_size
                if args.duration:
                    kwargs["duration_sec"] = args.duration
                    
            elif args.pattern == "spike":
                if args.target_percent:
                    kwargs["target_percent"] = args.target_percent
                if args.hold_time:
                    kwargs["hold_sec"] = args.hold_time
                    
            elif args.pattern == "sawtooth":
                if args.min_mb:
                    kwargs["min_mb"] = args.min_mb
                if args.max_mb:
                    kwargs["max_mb"] = args.max_mb
                if args.period:
                    kwargs["period_sec"] = args.period
                if args.cycles:
                    kwargs["cycles"] = args.cycles
            
            # Start the pressure pattern
            pressurer.start_pressure_pattern(args.pattern, **kwargs)
            
            # Wait for the duration if needed
            if "duration_sec" not in kwargs:
                try:
                    print(f"Pressure pattern running. Press Ctrl+C to stop...")
                    time.sleep(args.duration)
                except KeyboardInterrupt:
                    print("\nStopping memory pressure simulation...")
                finally:
                    pressurer.stop_pressure()
        else:
            # Use the existing function for backward compatibility
            simulate_memory_pressure(args.pattern, args.duration)
    elif args.command == "kb":
        run_knowledge_base_cli()
    else:
        # Default action: print welcome message
        print("VisionAI-ClipsMaster - Memory Safety Framework")
        print("===========================================")
        print("Commands:")
        print("  test         - Run memory safety tests")
        print("  simulate     - Simulate memory pressure")
        print("  kb           - Run knowledge base CLI")
        print("")
        print("Memory Pressure Patterns:")
        print("  steady_growth - Steady memory growth (legacy)")
        print("  spikes       - Memory usage spikes (legacy)")
        print("  leak         - Simulated memory leak (legacy)")
        print("  fragmentation - Memory fragmentation (legacy)")
        print("  mixed        - Mixed workload pattern (legacy)")
        print("  stepped      - Stepped memory growth pattern (new)")
        print("  spike        - Sudden memory usage spike (new)")
        print("  sawtooth     - Sawtooth pattern (new)")
        print("")
        print("Example:")
        print("  python main.py test")
        print("  python main.py simulate stepped --step-size 200 --duration 60")
        print("  python main.py simulate spike --target-percent 70 --hold-time 10")
        print("  python main.py kb list-patterns")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
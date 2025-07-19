import logging
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from .knowledge_base import KnowledgeBase

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KnowledgeService")

class KnowledgeService:
    """
    KnowledgeService integrates the knowledge base with the circuit-breaking system.
    It provides diagnosis capabilities and solution recommendations.
    """
    
    def __init__(self, 
                 knowledge_base: Optional[KnowledgeBase] = None,
                 log_analyzer = None,
                 event_tracer = None,
                 max_log_entries: int = 1000):
        """
        Initialize the KnowledgeService.
        
        Args:
            knowledge_base: KnowledgeBase instance or None to create a new one
            log_analyzer: LogAnalyzer instance for log analysis
            event_tracer: EventTracer instance for event recording
            max_log_entries: Maximum number of log entries to keep in memory
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.log_analyzer = log_analyzer
        self.event_tracer = event_tracer
        self.max_log_entries = max_log_entries
        
        # Recent log entries for analysis
        self.recent_logs: List[str] = []
        
        # Recently suggested solutions
        self.recent_solutions: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("KnowledgeService initialized")
    
    def analyze_logs(self, log_entries: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Analyze log entries for memory issue patterns.
        
        Args:
            log_entries: List of log entries to analyze, or None to use stored logs
            
        Returns:
            Dictionary of pattern IDs to matching log entries
        """
        if log_entries:
            # Add new logs to recent logs
            self.recent_logs.extend(log_entries)
            
            # Trim if exceeding max size
            if len(self.recent_logs) > self.max_log_entries:
                self.recent_logs = self.recent_logs[-self.max_log_entries:]
        
        # Match patterns in the logs
        matches = self.knowledge_base.match_log_patterns(self.recent_logs)
        
        if matches:
            logger.info(f"Found {sum(len(entries) for entries in matches.values())} log matches "
                       f"across {len(matches)} patterns")
        
        return matches
    
    def diagnose_issue(self, 
                      issue_description: str, 
                      log_entries: Optional[List[str]] = None,
                      circuit_break_events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Diagnose a memory issue based on description, logs, and events.
        
        Args:
            issue_description: Description of the issue
            log_entries: Optional log entries related to the issue
            circuit_break_events: Optional circuit break events
            
        Returns:
            Dictionary with diagnosis information and recommended solutions
        """
        # Step 1: Analyze logs if provided
        log_pattern_matches = {}
        if log_entries:
            log_pattern_matches = self.analyze_logs(log_entries)
        
        # Step 2: Get solutions based on issue description
        description_solutions = self.knowledge_base.get_solutions_for_issue(issue_description)
        
        # Step 3: Find patterns that match circuit break events
        event_pattern_matches = []
        if circuit_break_events and self.event_tracer:
            # Analyze events for patterns
            memory_usage_patterns = self._analyze_memory_usage_patterns(circuit_break_events)
            event_pattern_matches = self._match_memory_patterns(memory_usage_patterns)
        
        # Step 4: Combine all findings and rank solutions
        diagnosis = self._combine_diagnosis(
            issue_description,
            description_solutions,
            log_pattern_matches,
            event_pattern_matches
        )
        
        # Step 5: Store recent solutions
        issue_id = hash(issue_description) % 10000
        self.recent_solutions[str(issue_id)] = diagnosis["recommended_solutions"]
        
        return diagnosis
    
    def _analyze_memory_usage_patterns(self, 
                                      events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze memory usage patterns from circuit break events.
        
        Args:
            events: List of circuit break events
            
        Returns:
            Dictionary with memory usage pattern information
        """
        if not events:
            return {}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        # Extract memory usage values
        memory_usages = [e.get("memory_usage_mb", 0) for e in sorted_events]
        thresholds = [e.get("threshold_mb", 0) for e in sorted_events]
        timestamps = [e.get("timestamp", 0) for e in sorted_events]
        
        # Calculate memory growth rate
        memory_growth_rate = 0
        if len(memory_usages) >= 2 and timestamps[-1] > timestamps[0]:
            time_diff = timestamps[-1] - timestamps[0]
            usage_diff = memory_usages[-1] - memory_usages[0]
            memory_growth_rate = usage_diff / time_diff  # MB per second
        
        # Detect pattern type
        pattern_type = "unknown"
        if len(memory_usages) >= 3:
            # Check for steady growth
            differences = [memory_usages[i+1] - memory_usages[i] for i in range(len(memory_usages)-1)]
            avg_diff = sum(differences) / len(differences)
            variance = sum((d - avg_diff)**2 for d in differences) / len(differences)
            
            if variance < 0.1 * avg_diff and avg_diff > 0:
                pattern_type = "steady_growth"
            elif any(diff > 2 * avg_diff for diff in differences):
                pattern_type = "sudden_spikes"
            elif memory_usages[-1] < memory_usages[0]:
                pattern_type = "decreasing"
            elif max(memory_usages) - min(memory_usages) < 0.1 * max(memory_usages):
                pattern_type = "stable_high"
        
        return {
            "event_count": len(events),
            "avg_memory_usage": sum(memory_usages) / len(memory_usages) if memory_usages else 0,
            "max_memory_usage": max(memory_usages) if memory_usages else 0,
            "memory_growth_rate_mb_per_sec": memory_growth_rate,
            "threshold": thresholds[0] if thresholds else 0,
            "pattern_type": pattern_type,
            "first_timestamp": timestamps[0] if timestamps else 0,
            "last_timestamp": timestamps[-1] if timestamps else 0
        }
    
    def _match_memory_patterns(self, memory_pattern: Dict[str, Any]) -> List[str]:
        """
        Match memory usage patterns to known patterns.
        
        Args:
            memory_pattern: Memory usage pattern information
            
        Returns:
            List of matching pattern IDs
        """
        matches = []
        
        pattern_type = memory_pattern.get("pattern_type", "unknown")
        growth_rate = memory_pattern.get("memory_growth_rate_mb_per_sec", 0)
        
        # Pattern matching based on type and growth rate
        if pattern_type == "steady_growth" and growth_rate > 0.5:
            matches.append("LEAK_LARGE_NUMPY_ARRAY")
        
        if pattern_type == "sudden_spikes":
            matches.append("SUBTITLE_PARSING_OVERFLOW")
            matches.append("VIDEO_FRAME_CACHE_OVERFLOW")
        
        if pattern_type == "stable_high":
            matches.append("CASCADE_MEMORY_FRAGMENTATION")
        
        if pattern_type != "unknown" and memory_pattern.get("event_count", 0) > 5:
            matches.append("FFMPEG_RESOURCE_LEAK")
        
        return matches
    
    def _combine_diagnosis(self,
                          issue_description: str,
                          description_solutions: List[Dict[str, Any]],
                          log_pattern_matches: Dict[str, List[str]],
                          event_pattern_matches: List[str]) -> Dict[str, Any]:
        """
        Combine all diagnosis information and rank solutions.
        
        Args:
            issue_description: Description of the issue
            description_solutions: Solutions based on description
            log_pattern_matches: Pattern matches from logs
            event_pattern_matches: Pattern matches from events
            
        Returns:
            Dictionary with combined diagnosis information
        """
        # Collect all matching pattern IDs
        all_pattern_ids = set()
        for solution in description_solutions:
            all_pattern_ids.add(solution["pattern_id"])
        
        all_pattern_ids.update(log_pattern_matches.keys())
        all_pattern_ids.update(event_pattern_matches)
        
        # Calculate pattern scores
        pattern_scores: Dict[str, int] = {}
        for pattern_id in all_pattern_ids:
            score = 0
            
            # Score from description solutions
            for solution in description_solutions:
                if solution["pattern_id"] == pattern_id:
                    score += solution["relevance_score"] * 2
            
            # Score from log matches
            if pattern_id in log_pattern_matches:
                score += len(log_pattern_matches[pattern_id])
            
            # Score from event matches
            if pattern_id in event_pattern_matches:
                score += 3
            
            pattern_scores[pattern_id] = score
        
        # Get pattern details and solutions
        recommended_solutions = []
        for pattern_id, score in sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True):
            pattern = self.knowledge_base.get_pattern(pattern_id)
            if pattern:
                recommended_solutions.append({
                    "pattern_id": pattern_id,
                    "name": pattern.name,
                    "description": pattern.description,
                    "solutions": pattern.solutions,
                    "relevance_score": score,
                    "severity": pattern.severity
                })
        
        return {
            "issue_description": issue_description,
            "identified_patterns": list(all_pattern_ids),
            "log_matches": sum(len(matches) for matches in log_pattern_matches.values()),
            "event_matches": len(event_pattern_matches),
            "recommended_solutions": recommended_solutions
        }
    
    def get_solution_for_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get solutions for a specific pattern.
        
        Args:
            pattern_id: ID of the pattern
            
        Returns:
            Dictionary with pattern information and solutions
        """
        pattern = self.knowledge_base.get_pattern(pattern_id)
        if not pattern:
            return None
        
        return {
            "pattern_id": pattern_id,
            "name": pattern.name,
            "description": pattern.description,
            "solutions": pattern.solutions,
            "severity": pattern.severity
        }
    
    def add_custom_case(self, 
                       title: str,
                       description: str,
                       memory_pattern: str,
                       solution_applied: str,
                       result: str,
                       related_pattern_id: Optional[str] = None) -> str:
        """
        Add a custom case to the knowledge base.
        
        Args:
            title: Case title
            description: Issue description
            memory_pattern: Memory pattern observed
            solution_applied: Solution that was applied
            result: Result of applying the solution
            related_pattern_id: Related pattern ID, if any
            
        Returns:
            ID of the new case
        """
        case_id = f"case_{hash(title + description) % 10000}"
        
        case = {
            "id": case_id,
            "title": title,
            "description": description,
            "memory_pattern": memory_pattern,
            "solution_applied": solution_applied,
            "result": result,
            "related_pattern_id": related_pattern_id
        }
        
        self.knowledge_base.add_custom_case(case)
        
        logger.info(f"Added custom case: {title} (ID: {case_id})")
        return case_id
    
    def get_similar_cases(self, issue_description: str, max_cases: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar cases for an issue description.
        
        Args:
            issue_description: Description of the issue
            max_cases: Maximum number of cases to return
            
        Returns:
            List of similar cases
        """
        cases = []
        issue_lower = issue_description.lower()
        
        for case in self.knowledge_base.custom_cases:
            score = 0
            
            # Check title and description
            if case.get("title", "").lower() in issue_lower:
                score += 3
            
            case_desc = case.get("description", "").lower()
            if any(keyword in issue_lower for keyword in case_desc.split()):
                score += 2
            
            # Check memory pattern
            pattern = case.get("memory_pattern", "").lower()
            if any(keyword in issue_lower for keyword in pattern.split()):
                score += 1
            
            if score > 0:
                case_copy = case.copy()
                case_copy["relevance_score"] = score
                cases.append(case_copy)
        
        # Sort by relevance score (descending)
        cases.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return cases[:max_cases] 
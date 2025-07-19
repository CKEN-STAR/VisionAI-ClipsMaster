import argparse
import json
import os
import sys
import logging
from typing import Dict, List, Any, Optional
from .knowledge_base import KnowledgeBase, MemoryIssuePattern
from .knowledge_service import KnowledgeService

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KnowledgeBaseCLI")

class KnowledgeBaseCLI:
    """Command-line interface for the Memory Issue Knowledge Base."""
    
    def __init__(self):
        """Initialize the CLI with a knowledge base and service."""
        self.kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base")
        os.makedirs(self.kb_dir, exist_ok=True)
        
        self.patterns_file = os.path.join(self.kb_dir, "patterns.json")
        self.cases_file = os.path.join(self.kb_dir, "custom_cases.json")
        
        # Initialize knowledge base
        self.kb = KnowledgeBase(
            default_patterns_file=self.patterns_file if os.path.exists(self.patterns_file) else None,
            custom_cases_file=self.cases_file if os.path.exists(self.cases_file) else None
        )
        
        # Initialize knowledge service
        self.service = KnowledgeService(knowledge_base=self.kb)
        
        # Save default patterns if file doesn't exist
        if not os.path.exists(self.patterns_file):
            self.kb.save_patterns(self.patterns_file)
        
        # Save empty custom cases if file doesn't exist
        if not os.path.exists(self.cases_file):
            self.kb.save_custom_cases(self.cases_file)
    
    def setup_parser(self) -> argparse.ArgumentParser:
        """
        Set up the command-line argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Memory Issue Knowledge Base CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # List patterns command
        list_patterns_parser = subparsers.add_parser("list-patterns", help="List all patterns")
        list_patterns_parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed information")
        
        # Show pattern command
        show_pattern_parser = subparsers.add_parser("show-pattern", help="Show pattern details")
        show_pattern_parser.add_argument("pattern_id", help="Pattern ID to show")
        
        # Add pattern command
        add_pattern_parser = subparsers.add_parser("add-pattern", help="Add a new pattern")
        add_pattern_parser.add_argument("--file", "-f", help="JSON file with pattern data")
        
        # Remove pattern command
        remove_pattern_parser = subparsers.add_parser("remove-pattern", help="Remove a pattern")
        remove_pattern_parser.add_argument("pattern_id", help="Pattern ID to remove")
        
        # List cases command
        list_cases_parser = subparsers.add_parser("list-cases", help="List all custom cases")
        list_cases_parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed information")
        
        # Show case command
        show_case_parser = subparsers.add_parser("show-case", help="Show case details")
        show_case_parser.add_argument("case_id", help="Case ID to show")
        
        # Add case command
        add_case_parser = subparsers.add_parser("add-case", help="Add a new custom case")
        add_case_parser.add_argument("--file", "-f", help="JSON file with case data")
        add_case_parser.add_argument("--title", "-t", help="Case title")
        add_case_parser.add_argument("--description", "-d", help="Issue description")
        add_case_parser.add_argument("--pattern", "-p", help="Memory pattern observed")
        add_case_parser.add_argument("--solution", "-s", help="Solution applied")
        add_case_parser.add_argument("--result", "-r", help="Result of solution")
        add_case_parser.add_argument("--related", help="Related pattern ID")
        
        # Remove case command
        remove_case_parser = subparsers.add_parser("remove-case", help="Remove a custom case")
        remove_case_parser.add_argument("case_id", help="Case ID to remove")
        
        # Diagnose command
        diagnose_parser = subparsers.add_parser("diagnose", help="Diagnose a memory issue")
        diagnose_parser.add_argument("--description", "-d", required=True, help="Issue description")
        diagnose_parser.add_argument("--logs", "-l", help="Log file to analyze")
        
        # Find similar cases command
        similar_parser = subparsers.add_parser("find-similar", help="Find similar cases")
        similar_parser.add_argument("--description", "-d", required=True, help="Issue description")
        similar_parser.add_argument("--max", "-m", type=int, default=5, help="Maximum cases to return")
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments, or None to use sys.argv
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # Dispatch to appropriate command handler
        try:
            if parsed_args.command == "list-patterns":
                self.list_patterns(parsed_args.detailed)
            elif parsed_args.command == "show-pattern":
                self.show_pattern(parsed_args.pattern_id)
            elif parsed_args.command == "add-pattern":
                self.add_pattern(parsed_args.file)
            elif parsed_args.command == "remove-pattern":
                self.remove_pattern(parsed_args.pattern_id)
            elif parsed_args.command == "list-cases":
                self.list_cases(parsed_args.detailed)
            elif parsed_args.command == "show-case":
                self.show_case(parsed_args.case_id)
            elif parsed_args.command == "add-case":
                self.add_case(
                    parsed_args.file,
                    parsed_args.title,
                    parsed_args.description,
                    parsed_args.pattern,
                    parsed_args.solution,
                    parsed_args.result,
                    parsed_args.related
                )
            elif parsed_args.command == "remove-case":
                self.remove_case(parsed_args.case_id)
            elif parsed_args.command == "diagnose":
                self.diagnose(parsed_args.description, parsed_args.logs)
            elif parsed_args.command == "find-similar":
                self.find_similar(parsed_args.description, parsed_args.max)
            
            return 0
        except Exception as e:
            logger.error(f"Error: {e}")
            return 1
    
    def list_patterns(self, detailed: bool = False) -> None:
        """
        List all patterns in the knowledge base.
        
        Args:
            detailed: Whether to show detailed information
        """
        patterns = self.kb.get_all_patterns()
        
        if not patterns:
            print("No patterns found.")
            return
        
        print(f"Found {len(patterns)} patterns:")
        
        for pattern in patterns:
            if detailed:
                print(f"\nPattern: {pattern['name']} (ID: {pattern['id']})")
                print(f"Severity: {pattern['severity']}/5")
                print(f"Description: {pattern['description']}")
                print("Symptoms:")
                for symptom in pattern["symptoms"]:
                    print(f"  - {symptom}")
                print("Solutions:")
                for solution in pattern["solutions"]:
                    print(f"  - {solution}")
            else:
                print(f"- {pattern['name']} (ID: {pattern['id']}, Severity: {pattern['severity']}/5)")
    
    def show_pattern(self, pattern_id: str) -> None:
        """
        Show detailed information for a pattern.
        
        Args:
            pattern_id: ID of the pattern to show
        """
        pattern = self.kb.get_pattern(pattern_id)
        
        if not pattern:
            print(f"Pattern not found: {pattern_id}")
            return
        
        pattern_dict = pattern.to_dict()
        
        print(f"Pattern: {pattern_dict['name']} (ID: {pattern_dict['id']})")
        print(f"Severity: {pattern_dict['severity']}/5")
        print(f"Description: {pattern_dict['description']}")
        
        print("\nSymptoms:")
        for symptom in pattern_dict["symptoms"]:
            print(f"  - {symptom}")
        
        print("\nCauses:")
        for cause in pattern_dict["causes"]:
            print(f"  - {cause}")
        
        print("\nSolutions:")
        for solution in pattern_dict["solutions"]:
            print(f"  - {solution}")
        
        if pattern_dict.get("detection_regex"):
            print(f"\nDetection Regex: {pattern_dict['detection_regex']}")
        
        if pattern_dict.get("code_snippet"):
            print("\nCode Snippet:")
            print(pattern_dict["code_snippet"])
    
    def add_pattern(self, file_path: Optional[str]) -> None:
        """
        Add a pattern to the knowledge base.
        
        Args:
            file_path: Path to JSON file with pattern data
        """
        if not file_path:
            print("Error: JSON file is required")
            return
        
        try:
            with open(file_path, 'r') as f:
                pattern_data = json.load(f)
            
            pattern = MemoryIssuePattern.from_dict(pattern_data)
            self.kb.add_pattern(pattern)
            self.kb.save_patterns(self.patterns_file)
            
            print(f"Added pattern: {pattern.name} (ID: {pattern.pattern_id})")
        except Exception as e:
            print(f"Error adding pattern: {e}")
    
    def remove_pattern(self, pattern_id: str) -> None:
        """
        Remove a pattern from the knowledge base.
        
        Args:
            pattern_id: ID of the pattern to remove
        """
        if self.kb.remove_pattern(pattern_id):
            self.kb.save_patterns(self.patterns_file)
            print(f"Removed pattern: {pattern_id}")
        else:
            print(f"Pattern not found: {pattern_id}")
    
    def list_cases(self, detailed: bool = False) -> None:
        """
        List all custom cases in the knowledge base.
        
        Args:
            detailed: Whether to show detailed information
        """
        cases = self.kb.custom_cases
        
        if not cases:
            print("No custom cases found.")
            return
        
        print(f"Found {len(cases)} custom cases:")
        
        for case in cases:
            if detailed:
                print(f"\nCase: {case.get('title', 'Untitled')} (ID: {case.get('id', 'unknown')})")
                print(f"Description: {case.get('description', 'No description')}")
                print(f"Memory Pattern: {case.get('memory_pattern', 'Not specified')}")
                print(f"Solution Applied: {case.get('solution_applied', 'Not specified')}")
                print(f"Result: {case.get('result', 'Not specified')}")
                if case.get('related_pattern_id'):
                    print(f"Related Pattern: {case['related_pattern_id']}")
            else:
                print(f"- {case.get('title', 'Untitled')} (ID: {case.get('id', 'unknown')})")
    
    def show_case(self, case_id: str) -> None:
        """
        Show detailed information for a custom case.
        
        Args:
            case_id: ID of the case to show
        """
        case = None
        
        for c in self.kb.custom_cases:
            if c.get("id") == case_id:
                case = c
                break
        
        if not case:
            print(f"Custom case not found: {case_id}")
            return
        
        print(f"Case: {case.get('title', 'Untitled')} (ID: {case.get('id', 'unknown')})")
        print(f"Description: {case.get('description', 'No description')}")
        print(f"Memory Pattern: {case.get('memory_pattern', 'Not specified')}")
        print(f"Solution Applied: {case.get('solution_applied', 'Not specified')}")
        print(f"Result: {case.get('result', 'Not specified')}")
        
        if case.get('related_pattern_id'):
            related_pattern = self.kb.get_pattern(case['related_pattern_id'])
            print(f"Related Pattern: {case['related_pattern_id']}")
            
            if related_pattern:
                print(f"  {related_pattern.name}: {related_pattern.description}")
    
    def add_case(self, 
                file_path: Optional[str],
                title: Optional[str],
                description: Optional[str],
                pattern: Optional[str],
                solution: Optional[str],
                result: Optional[str],
                related: Optional[str]) -> None:
        """
        Add a custom case to the knowledge base.
        
        Args:
            file_path: Path to JSON file with case data
            title: Case title
            description: Issue description
            pattern: Memory pattern observed
            solution: Solution applied
            result: Result of solution
            related: Related pattern ID
        """
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    case_data = json.load(f)
                
                self.kb.add_custom_case(case_data)
                self.kb.save_custom_cases(self.cases_file)
                
                print(f"Added custom case from file: {file_path}")
                return
            except Exception as e:
                print(f"Error adding case from file: {e}")
                return
        
        if not title or not description or not pattern or not solution or not result:
            print("Error: All fields are required (title, description, pattern, solution, result)")
            return
        
        case_id = self.service.add_custom_case(
            title=title,
            description=description,
            memory_pattern=pattern,
            solution_applied=solution,
            result=result,
            related_pattern_id=related
        )
        
        self.kb.save_custom_cases(self.cases_file)
        
        print(f"Added custom case: {title} (ID: {case_id})")
    
    def remove_case(self, case_id: str) -> None:
        """
        Remove a custom case from the knowledge base.
        
        Args:
            case_id: ID of the case to remove
        """
        if self.kb.remove_custom_case(case_id):
            self.kb.save_custom_cases(self.cases_file)
            print(f"Removed custom case: {case_id}")
        else:
            print(f"Custom case not found: {case_id}")
    
    def diagnose(self, description: str, logs_file: Optional[str]) -> None:
        """
        Diagnose a memory issue.
        
        Args:
            description: Issue description
            logs_file: Path to log file
        """
        log_entries = []
        
        if logs_file and os.path.exists(logs_file):
            try:
                with open(logs_file, 'r') as f:
                    log_entries = f.readlines()
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        diagnosis = self.service.diagnose_issue(description, log_entries)
        
        print(f"Diagnosis for issue: {description}")
        print(f"Found {len(diagnosis['identified_patterns'])} potential matching patterns")
        print(f"Log matches: {diagnosis['log_matches']}")
        
        if diagnosis["recommended_solutions"]:
            print("\nRecommended solutions:")
            for i, solution in enumerate(diagnosis["recommended_solutions"], 1):
                print(f"\n{i}. {solution['name']} (Score: {solution['relevance_score']})")
                print(f"   Severity: {solution['severity']}/5")
                print(f"   Description: {solution['description']}")
                print("   Solutions:")
                for j, sol in enumerate(solution['solutions'], 1):
                    print(f"     {j}. {sol}")
        else:
            print("\nNo solutions found for this issue.")
    
    def find_similar(self, description: str, max_cases: int) -> None:
        """
        Find similar cases for an issue description.
        
        Args:
            description: Issue description
            max_cases: Maximum cases to return
        """
        similar_cases = self.service.get_similar_cases(description, max_cases)
        
        if not similar_cases:
            print("No similar cases found.")
            return
        
        print(f"Found {len(similar_cases)} similar cases for: {description}")
        
        for i, case in enumerate(similar_cases, 1):
            print(f"\n{i}. {case.get('title', 'Untitled')} (Score: {case.get('relevance_score', 0)})")
            print(f"   Description: {case.get('description', 'No description')}")
            print(f"   Solution: {case.get('solution_applied', 'Not specified')}")
            print(f"   Result: {case.get('result', 'Not specified')}")


def main():
    """Main entry point for the CLI."""
    cli = KnowledgeBaseCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main() 
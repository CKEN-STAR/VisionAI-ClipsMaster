#!/usr/bin/env python3
"""
VisionAI-ClipsMaster Health Check Script
Comprehensive health monitoring for Docker containers
"""

import sys
import time
import requests
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthChecker:
    """Comprehensive health checker for VisionAI-ClipsMaster services"""
    
    def __init__(self):
        self.services = {
            'main_app': {'url': 'http://localhost:8000', 'timeout': 30},
            'web_interface': {'url': 'http://localhost:8080', 'timeout': 30},
            'api': {'url': 'http://localhost:5000', 'timeout': 30},
            'redis': {'host': 'localhost', 'port': 6379},
            'postgres': {'host': 'localhost', 'port': 5432}
        }
        
        self.critical_paths = [
            '/app/models',
            '/app/data',
            '/app/output',
            '/app/logs',
            '/app/cache'
        ]
        
        self.health_status = {}
    
    def check_http_service(self, name: str, config: Dict) -> Tuple[bool, str]:
        """Check HTTP service health"""
        try:
            response = requests.get(
                f"{config['url']}/health",
                timeout=config.get('timeout', 10)
            )
            
            if response.status_code == 200:
                return True, f"{name} is healthy"
            else:
                return False, f"{name} returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, f"{name} connection refused"
        except requests.exceptions.Timeout:
            return False, f"{name} timeout"
        except Exception as e:
            return False, f"{name} error: {str(e)}"
    
    def check_tcp_service(self, name: str, config: Dict) -> Tuple[bool, str]:
        """Check TCP service health"""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((config['host'], config['port']))
            sock.close()
            
            if result == 0:
                return True, f"{name} is reachable"
            else:
                return False, f"{name} is not reachable"
                
        except Exception as e:
            return False, f"{name} error: {str(e)}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        try:
            usage = psutil.disk_usage('/')
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            percent_used = (usage.used / usage.total) * 100
            
            if percent_used > 90:
                return False, f"Disk space critical: {percent_used:.1f}% used"
            elif percent_used > 80:
                return True, f"Disk space warning: {percent_used:.1f}% used"
            else:
                return True, f"Disk space OK: {free_gb:.1f}GB free of {total_gb:.1f}GB"
                
        except Exception as e:
            return False, f"Disk check error: {str(e)}"
    
    def check_memory_usage(self) -> Tuple[bool, str]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            if percent_used > 90:
                return False, f"Memory critical: {percent_used:.1f}% used"
            elif percent_used > 80:
                return True, f"Memory warning: {percent_used:.1f}% used"
            else:
                return True, f"Memory OK: {percent_used:.1f}% used"
                
        except Exception as e:
            return False, f"Memory check error: {str(e)}"
    
    def check_critical_paths(self) -> Tuple[bool, str]:
        """Check if critical paths exist and are writable"""
        missing_paths = []
        unwritable_paths = []
        
        for path_str in self.critical_paths:
            path = Path(path_str)
            
            if not path.exists():
                missing_paths.append(path_str)
            elif not path.is_dir():
                missing_paths.append(f"{path_str} (not a directory)")
            else:
                # Check if writable
                try:
                    test_file = path / '.health_check_test'
                    test_file.touch()
                    test_file.unlink()
                except Exception:
                    unwritable_paths.append(path_str)
        
        if missing_paths:
            return False, f"Missing paths: {', '.join(missing_paths)}"
        elif unwritable_paths:
            return False, f"Unwritable paths: {', '.join(unwritable_paths)}"
        else:
            return True, "All critical paths are accessible"
    
    def check_python_imports(self) -> Tuple[bool, str]:
        """Check if critical Python modules can be imported"""
        critical_modules = [
            'torch',
            'transformers',
            'opencv-python',
            'PyQt6',
            'numpy',
            'pandas',
            'matplotlib'
        ]
        
        failed_imports = []
        
        for module in critical_modules:
            try:
                # Handle special cases
                if module == 'opencv-python':
                    import cv2
                elif module == 'PyQt6':
                    from PyQt6 import QtCore
                else:
                    __import__(module)
            except ImportError:
                failed_imports.append(module)
            except Exception as e:
                failed_imports.append(f"{module} ({str(e)})")
        
        if failed_imports:
            return False, f"Failed imports: {', '.join(failed_imports)}"
        else:
            return True, "All critical modules imported successfully"
    
    def run_comprehensive_check(self) -> Dict[str, Tuple[bool, str]]:
        """Run all health checks"""
        logger.info("Starting comprehensive health check...")
        
        results = {}
        
        # Check HTTP services
        for name, config in self.services.items():
            if 'url' in config:
                results[name] = self.check_http_service(name, config)
            else:
                results[name] = self.check_tcp_service(name, config)
        
        # Check system resources
        results['disk_space'] = self.check_disk_space()
        results['memory_usage'] = self.check_memory_usage()
        results['critical_paths'] = self.check_critical_paths()
        results['python_imports'] = self.check_python_imports()
        
        return results
    
    def print_results(self, results: Dict[str, Tuple[bool, str]]) -> bool:
        """Print health check results"""
        all_healthy = True
        
        print("\n" + "="*60)
        print("VisionAI-ClipsMaster Health Check Results")
        print("="*60)
        
        for check_name, (is_healthy, message) in results.items():
            status = "✓ PASS" if is_healthy else "✗ FAIL"
            color = "\033[92m" if is_healthy else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}{status}{reset} {check_name.replace('_', ' ').title()}: {message}")
            
            if not is_healthy:
                all_healthy = False
        
        print("="*60)
        
        if all_healthy:
            print("\033[92m✓ All health checks passed!\033[0m")
        else:
            print("\033[91m✗ Some health checks failed!\033[0m")
        
        print("="*60)
        
        return all_healthy

def main():
    """Main health check function"""
    checker = HealthChecker()
    
    try:
        results = checker.run_comprehensive_check()
        all_healthy = checker.print_results(results)
        
        # Exit with appropriate code
        sys.exit(0 if all_healthy else 1)
        
    except KeyboardInterrupt:
        logger.info("Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Health check failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

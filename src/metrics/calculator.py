"""
Metrics Calculator
Calculates code coverage and quality metrics
"""

import subprocess
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class MetricsCalculator:
    """Calculates code coverage and quality metrics"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.coverage_config = config.get('coverage', {})
        self.min_line_coverage = self.coverage_config.get('minimum_line_coverage', 0.95)
        self.min_branch_coverage = self.coverage_config.get('minimum_branch_coverage', 0.90)
        self.coverage_tool = self.coverage_config.get('tool', 'jacoco')
    
    def calculate_coverage(self, source_file: str, test_file: str,
                          output_dir: str = "htmlcov") -> Dict:
        """
        Calculate code coverage for source file using test file
        
        Args:
            source_file: Path to source file (Python or Java)
            test_file: Path to test file
            output_dir: Directory for coverage reports
            
        Returns:
            Dictionary with coverage metrics
        """
        return self._calculate_jacoco_coverage(source_file, test_file, output_dir)
    
    def _calculate_python_coverage(self, source_file: str, test_file: str, output_dir: str) -> Dict:
        """Calculate Python code coverage using pytest-cov"""
        source_path = Path(source_file)
        test_path = Path(test_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Run pytest with coverage
            cmd = [
                'pytest',
                str(test_path),
                '--cov', str(source_path.parent),
                '--cov-report', 'term-missing',
                '--cov-report', f'html:{output_path}',
                '--cov-report', 'json',
                '-v'
            ]
            
            print(f"Calculating coverage for {source_file}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse coverage from JSON report
            coverage_json_path = Path('coverage.json')
            if coverage_json_path.exists():
                with open(coverage_json_path, 'r') as f:
                    coverage_data = json.load(f)
                
                # Extract coverage for our specific file
                files = coverage_data.get('files', {})
                file_key = str(source_path.absolute())
                
                # Try different key formats
                file_coverage = None
                for key in files.keys():
                    if source_path.name in key or str(source_path) in key:
                        file_coverage = files[key]
                        break
                
                if file_coverage:
                    line_coverage = file_coverage.get('summary', {}).get('percent_covered', 0.0) / 100.0
                    branch_coverage = file_coverage.get('summary', {}).get('percent_covered_branches', 0.0) / 100.0
                    total_lines = file_coverage.get('summary', {}).get('num_statements', 0)
                    covered_lines = file_coverage.get('summary', {}).get('covered_lines', 0)
                else:
                    # Fallback: parse from terminal output
                    line_coverage, branch_coverage, total_lines, covered_lines = self._parse_coverage_output(result.stdout)
            else:
                # Parse from terminal output
                line_coverage, branch_coverage, total_lines, covered_lines = self._parse_coverage_output(result.stdout)
            
            # Check if thresholds are met
            line_threshold_met = line_coverage >= self.min_line_coverage
            branch_threshold_met = branch_coverage >= self.min_branch_coverage
            
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'line_coverage': line_coverage,
                'branch_coverage': branch_coverage,
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'min_line_coverage': self.min_line_coverage,
                'min_branch_coverage': self.min_branch_coverage,
                'line_threshold_met': line_threshold_met,
                'branch_threshold_met': branch_threshold_met,
                'pytest_passed': result.returncode == 0,
                'pytest_output': result.stdout,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'error': 'Coverage calculation timed out',
                'line_coverage': 0.0,
                'branch_coverage': 0.0
            }
        except Exception as e:
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'error': str(e),
                'line_coverage': 0.0,
                'branch_coverage': 0.0
            }
    
    def _calculate_jacoco_coverage(self, source_file: str, test_file: str, output_dir: str) -> Dict:
        """Calculate Java code coverage using JaCoCo"""
        from pathlib import Path
        import xml.etree.ElementTree as ET
        
        source_path = Path(source_file)
        project_root = self._find_maven_root(source_path)
        
        if not project_root:
            raise ValueError("Could not find Maven project root (pom.xml)")
        
        try:
            # Run Maven with JaCoCo
            cmd = ['mvn', 'clean', 'test', 'jacoco:report']
            
            print(f"Calculating JaCoCo coverage for {source_file}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=300
            )
            
            # Parse JaCoCo XML report
            jacoco_xml = Path(project_root) / 'target' / 'site' / 'jacoco' / 'jacoco.xml'
            if not jacoco_xml.exists():
                # Try alternative location
                jacoco_xml = Path(project_root) / 'target' / 'jacoco.exec'
                if not jacoco_xml.exists():
                    # Parse from console output
                    return self._parse_jacoco_output(result.stdout)
            
            # Parse XML report
            tree = ET.parse(jacoco_xml)
            root = tree.getroot()
            
            # Get coverage metrics from root counter
            counters = root.findall('.//counter[@type="LINE"]')
            if counters:
                covered = sum(int(c.get('covered', 0)) for c in counters)
                missed = sum(int(c.get('missed', 0)) for c in counters)
                total = covered + missed
                line_coverage = covered / total if total > 0 else 0.0
            else:
                line_coverage = 0.0
            
            branch_counters = root.findall('.//counter[@type="BRANCH"]')
            if branch_counters:
                covered = sum(int(c.get('covered', 0)) for c in branch_counters)
                missed = sum(int(c.get('missed', 0)) for c in branch_counters)
                total = covered + missed
                branch_coverage = covered / total if total > 0 else 0.0
            else:
                branch_coverage = 0.0
            
            line_threshold_met = line_coverage >= self.min_line_coverage
            branch_threshold_met = branch_coverage >= self.min_branch_coverage
            
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'line_coverage': line_coverage,
                'branch_coverage': branch_coverage,
                'total_lines': total if 'total' in locals() else 0,
                'covered_lines': covered if 'covered' in locals() else 0,
                'min_line_coverage': self.min_line_coverage,
                'min_branch_coverage': self.min_branch_coverage,
                'line_threshold_met': line_threshold_met,
                'branch_threshold_met': branch_threshold_met,
                'maven_passed': result.returncode == 0,
                'maven_output': result.stdout,
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'error': 'Coverage calculation timed out',
                'line_coverage': 0.0,
                'branch_coverage': 0.0
            }
        except Exception as e:
            return {
                'source_file': str(source_file),
                'test_file': str(test_file),
                'error': str(e),
                'line_coverage': 0.0,
                'branch_coverage': 0.0
            }
    
    def _find_maven_root(self, file_path: Path) -> Optional[Path]:
        """Find Maven project root by looking for pom.xml"""
        current = file_path.parent if file_path.is_file() else file_path
        while current != current.parent:
            if (current / 'pom.xml').exists():
                return current
            current = current.parent
        return None
    
    def _parse_jacoco_output(self, output: str) -> Dict:
        """Parse JaCoCo coverage from Maven output"""
        line_coverage = 0.0
        branch_coverage = 0.0
        
        # Look for coverage percentage in output
        coverage_pattern = r'Coverage\s+(\d+(?:\.\d+)?)%'
        match = re.search(coverage_pattern, output, re.IGNORECASE)
        if match:
            line_coverage = float(match.group(1)) / 100.0
        
        return {
            'source_file': '',
            'test_file': '',
            'line_coverage': line_coverage,
            'branch_coverage': branch_coverage,
            'total_lines': 0,
            'covered_lines': 0
        }
    
    def _parse_coverage_output(self, output: str) -> tuple:
        """Parse coverage from pytest output"""
        line_coverage = 0.0
        branch_coverage = 0.0
        total_lines = 0
        covered_lines = 0
        
        # Look for coverage percentage in output
        # Example: "TOTAL 100% 50 0 0 0"
        coverage_pattern = r'TOTAL\s+(\d+)%\s+(\d+)\s+\d+\s+\d+\s+\d+'
        match = re.search(coverage_pattern, output)
        if match:
            line_coverage = float(match.group(1)) / 100.0
            total_lines = int(match.group(2))
            covered_lines = int(total_lines * line_coverage)
        
        # Try to find branch coverage
        branch_pattern = r'(\d+)%\s+branch'
        branch_match = re.search(branch_pattern, output)
        if branch_match:
            branch_coverage = float(branch_match.group(1)) / 100.0
        
        return line_coverage, branch_coverage, total_lines, covered_lines


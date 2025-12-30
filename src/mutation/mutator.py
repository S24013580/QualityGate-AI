"""
Mutation Testing Integration
Runs mutation testing and calculates mutation scores
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class MutationTester:
    """Runs mutation testing using mutmut (Python) or PIT (Java)"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mutation_config = config.get('mutation', {})
        self.tool = self.mutation_config.get('tool', 'pit')
        self.threshold = self.mutation_config.get('threshold', 0.85)
    
    def run_mutation_testing(self, source_file: str, test_file: str,
                            output_dir: str = "mutmut-results") -> Dict:
        """
        Run mutation testing on source file with test file
        
        Args:
            source_file: Path to source file (Python or Java)
            test_file: Path to test file
            output_dir: Directory for mutation testing results
            
        Returns:
            Dictionary with mutation testing results
        """
        return self._run_pit(source_file, test_file, output_dir)
    
    def _run_mutmut(self, source_file: str, test_file: str, output_dir: str) -> Dict:
        """Run mutation testing using mutmut"""
        source_path = Path(source_file)
        test_path = Path(test_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Prepare mutmut command
        # mutmut needs the module path, not file path
        source_dir = source_path.parent
        module_name = source_path.stem
        
        # Change to source directory for mutmut
        original_cwd = Path.cwd()
        
        try:
            # Run mutmut
            cmd = [
                'mutmut',
                'run',
                '--paths-to-mutate', str(source_path),
                '--tests-dir', str(test_path.parent),
                '--test-timeout', '10'
            ]
            
            print(f"Running mutation testing on {source_file}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(source_dir)
            )
            
            # Get results
            results_cmd = ['mutmut', 'results']
            results_output = subprocess.run(
                results_cmd,
                capture_output=True,
                text=True,
                cwd=str(source_dir)
            )
            
            # Parse results
            mutation_results = self._parse_mutmut_results(results_output.stdout)
            
            # Calculate mutation score
            total_mutations = mutation_results.get('total', 0)
            killed_mutations = mutation_results.get('killed', 0)
            survived_mutations = mutation_results.get('survived', 0)
            
            if total_mutations > 0:
                mutation_score = killed_mutations / total_mutations
            else:
                mutation_score = 0.0
            
            # Check if threshold is met
            threshold_met = mutation_score >= self.threshold
            
            return {
                'tool': 'mutmut',
                'source_file': str(source_file),
                'test_file': str(test_file),
                'total_mutations': total_mutations,
                'killed_mutations': killed_mutations,
                'survived_mutations': survived_mutations,
                'mutation_score': mutation_score,
                'threshold': self.threshold,
                'threshold_met': threshold_met,
                'details': mutation_results.get('details', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.CalledProcessError as e:
            print(f"Error running mutation testing: {e}")
            return {
                'tool': 'mutmut',
                'error': str(e),
                'mutation_score': 0.0,
                'threshold_met': False
            }
        finally:
            pass  # Could restore original_cwd if needed
    
    def _parse_mutmut_results(self, output: str) -> Dict:
        """Parse mutmut results output"""
        results = {
            'total': 0,
            'killed': 0,
            'survived': 0,
            'timeout': 0,
            'suspicious': 0,
            'details': []
        }
        
        # Parse mutmut output format
        # Example: "To apply a mutant on disk run the same command with (or without) --apply=ID"
        # We need to count different statuses
        
        lines = output.split('\n')
        for line in lines:
            # Count mutations by status
            if 'killed' in line.lower():
                results['killed'] += 1
                results['total'] += 1
            elif 'survived' in line.lower():
                results['survived'] += 1
                results['total'] += 1
            elif 'timeout' in line.lower():
                results['timeout'] += 1
                results['total'] += 1
            elif 'suspicious' in line.lower():
                results['suspicious'] += 1
                results['total'] += 1
        
        # If we couldn't parse, try to get summary
        if results['total'] == 0:
            # Try alternative parsing
            match = re.search(r'(\d+)\s+mutants', output, re.IGNORECASE)
            if match:
                results['total'] = int(match.group(1))
        
        return results
    
    def get_mutation_details(self, source_file: str) -> List[Dict]:
        """Get detailed information about mutations"""
        source_path = Path(source_file)
        source_dir = source_path.parent
        
        try:
            # Get list of mutations
            cmd = ['mutmut', 'show']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(source_dir)
            )
            
            # Parse mutation details
            details = []
            # This would need more sophisticated parsing
            # For now, return empty list
            return details
            
        except Exception as e:
            print(f"Error getting mutation details: {e}")
            return []
    
    def _run_pit(self, source_file: str, test_file: str, output_dir: str) -> Dict:
        """Run mutation testing using PIT (Java)"""
        from pathlib import Path
        
        source_path = Path(source_file)
        project_root = self._find_maven_root(source_path)
        
        if not project_root:
            raise ValueError("Could not find Maven project root (pom.xml)")
        
        try:
            # Run PIT via Maven
            cmd = [
                'mvn',
                'org.pitest:pitest-maven:mutationCoverage',
                f'-DoutputDirectory={output_dir}'
            ]
            
            print(f"Running PIT mutation testing on {source_file}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=600  # 10 minutes
            )
            
            # Parse PIT results from XML
            pit_xml = Path(project_root) / output_dir / "mutations.xml"
            if pit_xml.exists():
                mutation_results = self._parse_pit_xml(pit_xml)
            else:
                # Try to parse from console output
                mutation_results = self._parse_pit_output(result.stdout)
            
            total_mutations = mutation_results.get('total', 0)
            killed_mutations = mutation_results.get('killed', 0)
            survived_mutations = mutation_results.get('survived', 0)
            
            if total_mutations > 0:
                mutation_score = killed_mutations / total_mutations
            else:
                mutation_score = 0.0
            
            threshold_met = mutation_score >= self.threshold
            
            return {
                'tool': 'pit',
                'source_file': str(source_file),
                'test_file': str(test_file),
                'total_mutations': total_mutations,
                'killed_mutations': killed_mutations,
                'survived_mutations': survived_mutations,
                'mutation_score': mutation_score,
                'threshold': self.threshold,
                'threshold_met': threshold_met,
                'details': mutation_results.get('details', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'tool': 'pit',
                'error': 'PIT mutation testing timed out',
                'mutation_score': 0.0,
                'threshold_met': False
            }
        except Exception as e:
            print(f"Error running PIT mutation testing: {e}")
            return {
                'tool': 'pit',
                'error': str(e),
                'mutation_score': 0.0,
                'threshold_met': False
            }
    
    def _find_maven_root(self, file_path: Path) -> Optional[Path]:
        """Find Maven project root by looking for pom.xml"""
        current = file_path.parent if file_path.is_file() else file_path
        while current != current.parent:
            if (current / 'pom.xml').exists():
                return current
            current = current.parent
        return None
    
    def _parse_pit_xml(self, xml_path: Path) -> Dict:
        """Parse PIT mutations.xml file"""
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            mutations = root.findall('.//mutation')
            total = len(mutations)
            killed = len([m for m in mutations if m.get('status') == 'KILLED'])
            survived = len([m for m in mutations if m.get('status') == 'SURVIVED'])
            
            return {
                'total': total,
                'killed': killed,
                'survived': survived,
                'details': []
            }
        except Exception as e:
            print(f"Error parsing PIT XML: {e}")
            return {'total': 0, 'killed': 0, 'survived': 0, 'details': []}
    
    def _parse_pit_output(self, output: str) -> Dict:
        """Parse PIT console output"""
        # Look for mutation score in output
        # Example: "Mutation score: 85%"
        match = re.search(r'Mutation score[:\s]+(\d+(?:\.\d+)?)%', output, re.IGNORECASE)
        if match:
            score = float(match.group(1)) / 100.0
            # Estimate mutations (rough)
            total_match = re.search(r'(\d+)\s+mutants?', output, re.IGNORECASE)
            total = int(total_match.group(1)) if total_match else 100
            killed = int(total * score)
            survived = total - killed
            
            return {
                'total': total,
                'killed': killed,
                'survived': survived,
                'details': []
            }
        
        return {'total': 0, 'killed': 0, 'survived': 0, 'details': []}


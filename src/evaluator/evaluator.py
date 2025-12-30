"""
Evaluator
Orchestrates test generation, mutation testing, and metrics collection
"""

import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..generator.java_test_generator import JavaTestGenerator
from ..mutation.mutator import MutationTester
from ..metrics.calculator import MetricsCalculator
from ..llm.factory import create_llm_client, load_config


class Evaluator:
    """Main evaluator that orchestrates the evaluation workflow"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.llm_client = create_llm_client(self.config)
        self.test_generator = JavaTestGenerator(self.llm_client, self.config)
        self.mutation_tester = MutationTester(self.config)
        self.metrics_calculator = MetricsCalculator(self.config)
    
    def evaluate_module(self, source_file: str, output_dir: str = "tests/generated",
                       protocol: Optional[str] = None) -> Dict:
        """
        Complete evaluation of a module
        
        Args:
            source_file: Path to source Python file
            output_dir: Directory for generated tests
            protocol: Prompt protocol level
            
        Returns:
            Complete evaluation results
        """
        start_time = time.time()
        
        # Step 1: Generate tests
        print(f"\n{'='*60}")
        print(f"Step 1: Generating tests for {source_file}")
        print(f"{'='*60}")
        
        try:
            test_file = self.test_generator.generate_tests(
                source_file=source_file,
                output_dir=output_dir,
                protocol=protocol
            )
            generation_time = time.time() - start_time
        except Exception as e:
            return {
                'source_file': source_file,
                'error': f"Test generation failed: {str(e)}",
                'success': False
            }
        
        # Step 2: Calculate coverage
        print(f"\n{'='*60}")
        print(f"Step 2: Calculating code coverage")
        print(f"{'='*60}")
        
        coverage_start = time.time()
        coverage_results = self.metrics_calculator.calculate_coverage(
            source_file=source_file,
            test_file=test_file,
            output_dir="htmlcov"
        )
        coverage_time = time.time() - coverage_start
        
        # Step 3: Run mutation testing
        print(f"\n{'='*60}")
        print(f"Step 3: Running mutation testing")
        print(f"{'='*60}")
        
        mutation_start = time.time()
        mutation_results = self.mutation_tester.run_mutation_testing(
            source_file=source_file,
            test_file=test_file,
            output_dir="mutmut-results"
        )
        mutation_time = time.time() - mutation_start
        
        total_time = time.time() - start_time
        
        # Compile results
        results = {
            'source_file': source_file,
            'test_file': test_file,
            'success': True,
            'timing': {
                'generation_time': generation_time,
                'coverage_time': coverage_time,
                'mutation_time': mutation_time,
                'total_time': total_time
            },
            'coverage': coverage_results,
            'mutation': mutation_results,
            'summary': {
                'line_coverage': coverage_results.get('line_coverage', 0.0),
                'mutation_score': mutation_results.get('mutation_score', 0.0),
                'thresholds_met': {
                    'coverage': coverage_results.get('line_threshold_met', False),
                    'mutation': mutation_results.get('threshold_met', False)
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return results
    
    def evaluate_all(self, baseline_file: str, experimental_file: str,
                    output_dir: str = "tests/generated") -> Dict:
        """
        Evaluate both baseline and experimental modules
        
        Args:
            baseline_file: Path to baseline (simple) module
            experimental_file: Path to experimental (complex) module
            output_dir: Directory for generated tests
            
        Returns:
            Comparative evaluation results
        """
        print(f"\n{'='*80}")
        print(f"COMPLETE EVALUATION: Baseline vs Experimental")
        print(f"{'='*80}\n")
        
        # Evaluate baseline
        print("EVALUATING BASELINE MODULE (Simple CRUD)")
        baseline_results = self.evaluate_module(
            source_file=baseline_file,
            output_dir=f"{output_dir}/baseline"
        )
        
        print("\n" + "="*80 + "\n")
        
        # Evaluate experimental
        print("EVALUATING EXPERIMENTAL MODULE (Complex Service)")
        experimental_results = self.evaluate_module(
            source_file=experimental_file,
            output_dir=f"{output_dir}/experimental",
            protocol="expert"  # Use expert protocol for complex module
        )
        
        # Comparative analysis
        comparison = {
            'baseline': baseline_results,
            'experimental': experimental_results,
            'comparison': {
                'coverage_difference': (
                    experimental_results.get('summary', {}).get('line_coverage', 0.0) -
                    baseline_results.get('summary', {}).get('line_coverage', 0.0)
                ),
                'mutation_score_difference': (
                    experimental_results.get('summary', {}).get('mutation_score', 0.0) -
                    baseline_results.get('summary', {}).get('mutation_score', 0.0)
                ),
                'time_difference': (
                    experimental_results.get('timing', {}).get('total_time', 0.0) -
                    baseline_results.get('timing', {}).get('total_time', 0.0)
                )
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return comparison


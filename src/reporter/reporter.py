"""
Report Generator
Creates HTML and text reports from evaluation results
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from jinja2 import Template


class ReportGenerator:
    """Generates evaluation reports"""
    
    HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>QualityGate-AI Evaluation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { background: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .metric { display: inline-block; margin: 10px 20px; padding: 15px; background: white; border-radius: 5px; min-width: 200px; }
        .metric-label { font-weight: bold; color: #7f8c8d; font-size: 0.9em; }
        .metric-value { font-size: 2em; color: #2c3e50; margin-top: 5px; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .comparison { display: flex; justify-content: space-around; margin: 20px 0; }
        .module-results { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>QualityGate-AI Evaluation Report</h1>
        <p><strong>Generated:</strong> {{ timestamp }}</p>
        
        {% if comparison %}
        <h2>Comparative Analysis</h2>
        <div class="comparison">
            <div class="module-results">
                <h3>Baseline Module (Simple CRUD)</h3>
                <div class="metric">
                    <div class="metric-label">Line Coverage</div>
                    <div class="metric-value">{{ "%.1f"|format(baseline_coverage * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Mutation Score</div>
                    <div class="metric-value">{{ "%.1f"|format(baseline_mutation * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Time</div>
                    <div class="metric-value">{{ "%.1f"|format(baseline_time) }}s</div>
                </div>
            </div>
            
            <div class="module-results">
                <h3>Experimental Module (Complex Service)</h3>
                <div class="metric">
                    <div class="metric-label">Line Coverage</div>
                    <div class="metric-value">{{ "%.1f"|format(experimental_coverage * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Mutation Score</div>
                    <div class="metric-value">{{ "%.1f"|format(experimental_mutation * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Time</div>
                    <div class="metric-value">{{ "%.1f"|format(experimental_time) }}s</div>
                </div>
            </div>
        </div>
        {% else %}
        <h2>Evaluation Results</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-label">Line Coverage</div>
                <div class="metric-value {% if coverage_met %}success{% else %}error{% endif %}">
                    {{ "%.1f"|format(line_coverage * 100) }}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Mutation Score</div>
                <div class="metric-value {% if mutation_met %}success{% else %}error{% endif %}">
                    {{ "%.1f"|format(mutation_score * 100) }}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Time</div>
                <div class="metric-value">{{ "%.1f"|format(total_time) }}s</div>
            </div>
        </div>
        {% endif %}
        
        <h2>Detailed Results</h2>
        <pre>{{ detailed_results }}</pre>
    </div>
</body>
</html>"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, results: Dict, filename: Optional[str] = None) -> str:
        """
        Generate HTML report from evaluation results
        
        Args:
            results: Evaluation results dictionary
            filename: Optional filename (defaults to timestamp-based)
            
        Returns:
            Path to generated report
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.html"
        
        report_path = self.output_dir / filename
        
        # Check if this is a comparison report
        is_comparison = 'comparison' in results
        
        if is_comparison:
            template_vars = {
                'timestamp': results.get('timestamp', datetime.now().isoformat()),
                'comparison': True,
                'baseline_coverage': results.get('baseline', {}).get('summary', {}).get('line_coverage', 0.0),
                'baseline_mutation': results.get('baseline', {}).get('summary', {}).get('mutation_score', 0.0),
                'baseline_time': results.get('baseline', {}).get('timing', {}).get('total_time', 0.0),
                'experimental_coverage': results.get('experimental', {}).get('summary', {}).get('line_coverage', 0.0),
                'experimental_mutation': results.get('experimental', {}).get('summary', {}).get('mutation_score', 0.0),
                'experimental_time': results.get('experimental', {}).get('timing', {}).get('total_time', 0.0),
                'detailed_results': json.dumps(results, indent=2)
            }
        else:
            summary = results.get('summary', {})
            template_vars = {
                'timestamp': results.get('timestamp', datetime.now().isoformat()),
                'comparison': False,
                'line_coverage': summary.get('line_coverage', 0.0),
                'mutation_score': summary.get('mutation_score', 0.0),
                'total_time': results.get('timing', {}).get('total_time', 0.0),
                'coverage_met': summary.get('thresholds_met', {}).get('coverage', False),
                'mutation_met': summary.get('thresholds_met', {}).get('mutation', False),
                'detailed_results': json.dumps(results, indent=2)
            }
        
        template = Template(self.HTML_TEMPLATE)
        html_content = template.render(**template_vars)
        
        report_path.write_text(html_content)
        print(f"\nReport generated: {report_path}")
        
        return str(report_path)
    
    def generate_json_report(self, results: Dict, filename: Optional[str] = None) -> str:
        """Generate JSON report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.json"
        
        report_path = self.output_dir / filename
        report_path.write_text(json.dumps(results, indent=2))
        
        return str(report_path)


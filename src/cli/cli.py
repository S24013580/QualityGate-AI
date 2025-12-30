"""
Command-line interface for QualityGate-AI
"""

import click
import sys
from pathlib import Path
from colorama import init, Fore, Style

from ..evaluator.evaluator import Evaluator
from ..reporter.reporter import ReportGenerator
from ..llm.factory import load_config, create_llm_client

# Initialize colorama for cross-platform colored output
init(autoreset=True)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """QualityGate-AI: Evaluation of Generative AI for Automated Unit Testing"""
    pass


@cli.command()
@click.option('--module', '-m', required=True, help='Path to Java source file (.java)')
@click.option('--output', '-o', default='tests/generated', help='Output directory for generated tests')
@click.option('--protocol', '-p', type=click.Choice(['standard', 'advanced', 'expert']),
              help='Prompt protocol level')
@click.option('--config', '-c', default='config/config.yaml', help='Configuration file path')
def generate(module, output, protocol, config):
    """Generate JUnit 5 tests for a Java class using AI"""
    try:
        config_data = load_config(config)
        llm_client = create_llm_client(config_data)
        
        # Check if LLM is available
        try:
            if not llm_client.is_available():
                click.echo(f"{Fore.RED}Error: LLM service is not available. Please check your configuration.", err=True)
                provider = config_data.get('llm', {}).get('provider', 'unknown')
                if provider == 'ollama':
                    click.echo(f"{Fore.YELLOW}For Ollama: Make sure Ollama is running and the model is installed.", err=True)
                    click.echo(f"{Fore.YELLOW}  Example: ollama pull codellama", err=True)
                elif provider in ['openai', 'chatgpt']:
                    click.echo(f"{Fore.YELLOW}For OpenAI: Make sure your API key is set correctly.", err=True)
                    click.echo(f"{Fore.YELLOW}  Set it with: export OPENAI_API_KEY='sk-your-key'", err=True)
                    click.echo(f"{Fore.YELLOW}  Or add it to config.yaml under llm.api_key", err=True)
                sys.exit(1)
        except ValueError as e:
            # API key validation error
            click.echo(f"{Fore.RED}Error: {str(e)}", err=True)
            click.echo(f"{Fore.YELLOW}Please check your OpenAI API key configuration.", err=True)
            sys.exit(1)
        
        from ..generator.java_test_generator import JavaTestGenerator
        generator = JavaTestGenerator(llm_client, config_data)
        
        click.echo(f"{Fore.CYAN}Generating Java tests for {module}...")
        test_file = generator.generate_tests(
            source_file=module,
            output_dir=output,
            protocol=protocol
        )
        
        click.echo(f"{Fore.GREEN}✓ Tests generated successfully: {test_file}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--module', '-m', required=True, help='Path to Java source file (.java)')
@click.option('--tests', '-t', help='Path to test file (if not provided, will generate)')
@click.option('--protocol', '-p', type=click.Choice(['standard', 'advanced', 'expert']),
              help='Prompt protocol level (if generating tests)')
@click.option('--config', '-c', default='config/config.yaml', help='Configuration file path')
@click.option('--report', '-r', is_flag=True, help='Generate HTML report')
def evaluate(module, tests, protocol, config, report):
    """Evaluate a module with generated or existing tests"""
    try:
        evaluator = Evaluator(config)
        
        # Generate tests if not provided
        if not tests:
            click.echo(f"{Fore.YELLOW}No test file provided. Generating tests first...")
            from ..llm.factory import load_config, create_llm_client
            from ..generator.java_test_generator import JavaTestGenerator
            
            config_data = load_config(config)
            llm_client = create_llm_client(config_data)
            generator = JavaTestGenerator(llm_client, config_data)
            
            test_file = generator.generate_tests(
                source_file=module,
                output_dir='tests/generated',
                protocol=protocol
            )
            tests = test_file
        
        click.echo(f"{Fore.CYAN}Running evaluation...")
        results = evaluator.evaluate_module(
            source_file=module,
            output_dir=Path(tests).parent,
            protocol=protocol
        )
        
        # Display results
        click.echo(f"\n{Fore.CYAN}{'='*60}")
        click.echo(f"{Fore.CYAN}EVALUATION RESULTS")
        click.echo(f"{Fore.CYAN}{'='*60}")
        
        summary = results.get('summary', {})
        click.echo(f"\n{Fore.GREEN}Line Coverage: {summary.get('line_coverage', 0.0)*100:.1f}%")
        click.echo(f"{Fore.GREEN}Mutation Score: {summary.get('mutation_score', 0.0)*100:.1f}%")
        
        timing = results.get('timing', {})
        click.echo(f"\n{Fore.YELLOW}Timing:")
        click.echo(f"  Generation: {timing.get('generation_time', 0.0):.2f}s")
        click.echo(f"  Coverage: {timing.get('coverage_time', 0.0):.2f}s")
        click.echo(f"  Mutation: {timing.get('mutation_time', 0.0):.2f}s")
        click.echo(f"  Total: {timing.get('total_time', 0.0):.2f}s")
        
        # Generate report if requested
        if report:
            reporter = ReportGenerator()
            report_path = reporter.generate_report(results)
            click.echo(f"\n{Fore.GREEN}Report generated: {report_path}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command(name='evaluate-all')
@click.option('--baseline', '-b', required=True, help='Path to baseline (simple) module')
@click.option('--experimental', '-e', required=True, help='Path to experimental (complex) module')
@click.option('--config', '-c', default='config/config.yaml', help='Configuration file path')
@click.option('--report', '-r', is_flag=True, default=True, help='Generate HTML report')
def evaluate_all(baseline, experimental, config, report):
    """Run complete evaluation comparing baseline and experimental modules"""
    try:
        evaluator = Evaluator(config)
        
        click.echo(f"{Fore.CYAN}Running complete evaluation...")
        results = evaluator.evaluate_all(
            baseline_file=baseline,
            experimental_file=experimental,
            output_dir='tests/generated'
        )
        
        # Display comparison
        click.echo(f"\n{Fore.CYAN}{'='*80}")
        click.echo(f"{Fore.CYAN}COMPARATIVE EVALUATION RESULTS")
        click.echo(f"{Fore.CYAN}{'='*80}")
        
        baseline_summary = results.get('baseline', {}).get('summary', {})
        experimental_summary = results.get('experimental', {}).get('summary', {})
        
        click.echo(f"\n{Fore.YELLOW}Baseline Module (Simple CRUD):")
        click.echo(f"  Coverage: {baseline_summary.get('line_coverage', 0.0)*100:.1f}%")
        click.echo(f"  Mutation Score: {baseline_summary.get('mutation_score', 0.0)*100:.1f}%")
        
        click.echo(f"\n{Fore.YELLOW}Experimental Module (Complex Service):")
        click.echo(f"  Coverage: {experimental_summary.get('line_coverage', 0.0)*100:.1f}%")
        click.echo(f"  Mutation Score: {experimental_summary.get('mutation_score', 0.0)*100:.1f}%")
        
        comparison = results.get('comparison', {})
        click.echo(f"\n{Fore.CYAN}Differences:")
        click.echo(f"  Coverage: {comparison.get('coverage_difference', 0.0)*100:+.1f}%")
        click.echo(f"  Mutation Score: {comparison.get('mutation_score_difference', 0.0)*100:+.1f}%")
        click.echo(f"  Time: {comparison.get('time_difference', 0.0):+.2f}s")
        
        # Generate report
        if report:
            reporter = ReportGenerator()
            report_path = reporter.generate_report(results)
            json_path = reporter.generate_json_report(results)
            click.echo(f"\n{Fore.GREEN}Reports generated:")
            click.echo(f"  HTML: {report_path}")
            click.echo(f"  JSON: {json_path}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config/config.yaml', help='Configuration file path')
def check(config):
    """Check if LLM service is available and configured correctly"""
    try:
        config_data = load_config(config)
        llm_client = create_llm_client(config_data)
        
        click.echo(f"{Fore.CYAN}Checking LLM configuration...")
        click.echo(f"Provider: {config_data.get('llm', {}).get('provider', 'unknown')}")
        click.echo(f"Model: {config_data.get('llm', {}).get('model', 'unknown')}")
        
        try:
            if llm_client.is_available():
                click.echo(f"{Fore.GREEN}✓ LLM service is available and ready")
            else:
                click.echo(f"{Fore.RED}✗ LLM service is not available")
                click.echo(f"{Fore.YELLOW}Please check:")
                provider = config_data.get('llm', {}).get('provider', 'unknown')
                if provider == 'ollama':
                    click.echo(f"  1. Is Ollama running? (ollama serve)")
                    click.echo(f"  2. Is the model installed? (ollama pull {config_data.get('llm', {}).get('model', 'codellama')})")
                elif provider in ['openai', 'chatgpt']:
                    click.echo(f"  1. Is your API key set correctly? (check config.yaml or OPENAI_API_KEY env var)")
                    click.echo(f"  2. Is your API key valid? (check at https://platform.openai.com/api-keys)")
                    click.echo(f"  3. Do you have credits in your OpenAI account?")
                else:
                    click.echo(f"  1. Is the model path correct?")
                    click.echo(f"  2. Do you have sufficient disk space?")
                sys.exit(1)
        except ValueError as e:
            # API key validation error
            click.echo(f"{Fore.RED}✗ {str(e)}")
            click.echo(f"{Fore.YELLOW}Please check your OpenAI API key configuration.")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}", err=True)
        sys.exit(1)


def main():
    """Entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()


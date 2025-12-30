# QualityGate-AI: Test Generation Tool

A standalone Python tool for generating and evaluating AI-assisted unit tests using a Hybrid Human-in-the-Loop methodology.

**Note:** This is a **separate tool** that can be used with any Java project. The research Java code is in a completely separate project (`QualityGate-AI-Research`).

## Overview

This tool implements a comprehensive evaluation framework for using Large Language Models (LLMs) to generate unit tests. It addresses the critical challenge of AI "hallucination" in code generation by:

- **Quality Assessment**: Using Mutation Testing to evaluate true defect-detection capability
- **Reliability Analysis**: Quantifying AI errors for complex vs simple business logic
- **Efficiency Measurement**: Tracking development cycle time reduction

## Features

- 🤖 **AI Test Generation**: Generate unit tests using free LLMs (Ollama/Hugging Face)
- 🧪 **Mutation Testing**: Automated quality assessment using mutation analysis (PIT for Java, mutmut for Python)
- 📊 **Metrics Tracking**: Line coverage, mutation score, and efficiency metrics (JaCoCo for Java, pytest-cov for Python)
- 🎯 **Prompt Engineering**: Structured protocol for optimal test generation
- 📈 **Comparative Analysis**: Evaluate AI-generated tests vs manual tests
- 🔧 **Multi-Language**: Supports Java and Python

## Architecture

```
QualityGate-AI/          (Test Generation Tool - Standalone)
├── src/
│   ├── llm/              # LLM integration (Ollama/Hugging Face)
│   ├── generator/        # Test generation engine
│   ├── mutation/         # Mutation testing integration
│   ├── metrics/          # Coverage and quality metrics
│   ├── prompts/          # Prompt engineering protocols
│   ├── cli/              # Command-line interface
│   ├── evaluator/        # Evaluation orchestrator
│   └── reporter/         # Report generation
├── config/              # Configuration files
└── reports/             # Evaluation reports (generated)

QualityGate-AI-Research/ (Separate Java Project - Research Code)
├── src/
│   ├── main/java/       # Java source code (Service Layer)
│   └── test/java/       # Generated tests
└── pom.xml              # Maven configuration
```

**Note:** These are two completely separate projects with no dependencies between them.

## Installation

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed (for free LLM) OR Hugging Face transformers

### Setup

```bash
# Navigate to project directory
cd QualityGate-AI

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama (if using - recommended)
# Visit https://ollama.ai/ and install, then:
ollama pull codellama  # or llama2, mistral, etc.

# Verify installation
python -m src.cli check
```

## Usage

### Basic Test Generation (Java)

```bash
# Generate tests for a Java class
python3 -m src.cli generate \
  --module /path/to/YourService.java \
  --output /path/to/test/directory \
  --protocol standard

# Generate with specific protocol level
python3 -m src.cli generate \
  --module /path/to/YourService.java \
  --output /path/to/test/directory \
  --protocol expert
```

### Evaluate a Module

```bash
# Evaluate with auto-generated tests (includes coverage and mutation testing)
python3 -m src.cli evaluate \
  --module /path/to/YourService.java \
  --report

# Evaluate with existing tests
python3 -m src.cli evaluate \
  --module /path/to/YourService.java \
  --tests /path/to/YourServiceTest.java
```

### Full Evaluation Workflow

```bash
# Run complete evaluation pipeline (baseline vs experimental)
python3 -m src.cli evaluate-all \
  --baseline /path/to/SimpleService.java \
  --experimental /path/to/ComplexService.java
```

### Check LLM Availability

```bash
# Verify LLM service is configured correctly
python -m src.cli check
```

## Using with Research Project

See `USING_WITH_RESEARCH_PROJECT.md` for detailed instructions on using this tool with the separate research project.

## Configuration

Edit `config/config.yaml` to customize:
- Language support (Java/Python)
- LLM model selection
- Prompt engineering parameters
- Mutation testing thresholds
- Coverage requirements

## Research Methodology

This tool supports research on AI-generated unit testing:

1. **Baseline Module**: Simple service (low complexity)
2. **Experimental Module**: Complex service (nested conditionals, temporal logic)
3. **Evaluation**: Mutation testing with quality metrics
4. **Comparison**: AI-generated vs manual tests

## Results Interpretation

- **Mutation Score**: Percentage of injected faults detected (target: >90%)
- **Line Coverage**: Code coverage percentage (target: 100%)
- **Efficiency Gain**: Time reduction vs manual testing (target: >70%)

## Documentation

- **QUICKSTART.md** - Quick start guide
- **PROJECT_STRUCTURE.md** - Detailed project structure
- **PROJECT_SEPARATION.md** - How projects are separated
- **USING_WITH_RESEARCH_PROJECT.md** - Integration guide
- **NEXT_STEPS.md** - Step-by-step workflow

## License

Research project for academic/industrial evaluation.

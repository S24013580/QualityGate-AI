# CI/CD Workflows

This directory contains GitHub Actions workflows for QualityGate-AI **tool only**.

## Workflows

### `ci.yml` - Tool Validation Pipeline

This workflow validates the tool itself:
- Verifies tool installation
- Tests CLI commands
- Validates LLM connectivity

**Note:** This workflow does NOT generate tests. For full test generation workflow, see the **Research Project** repository (`.github/workflows/ci.yml`).

## Full CI/CD Pipeline

The complete test generation workflow is in the **Research Project** repository because:

1. **Research Project** contains the Java code to test
2. **Research Project** needs to compile and run tests
3. **Tool Project** is checked out as a dependency
4. **Separation** is maintained between projects

See: `QualityGate-AI-Research/.github/workflows/ci.yml`

## How It Works

The research project's CI/CD:
1. Checks out research project (Java code)
2. Checks out this tool project (test generator)
3. Tool generates tests for research project
4. Research project compiles and runs tests
5. Reports are generated and uploaded

## Local Testing

To test the tool locally:

```bash
# Install act (GitHub Actions runner)
brew install act

# Run the workflow
act push
```


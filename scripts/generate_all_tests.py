#!/usr/bin/env python3
"""
Script to generate unit tests for all Java classes in the research project.
This is used in CI/CD pipeline to automatically generate tests.
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path so we can import src modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import using absolute imports from src
try:
    from src.llm.factory import load_config, create_llm_client
    from src.generator.java_test_generator import JavaTestGenerator
except ImportError as e:
    # Fallback: try adding src to path
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from llm.factory import load_config, create_llm_client
    from generator.java_test_generator import JavaTestGenerator


def find_java_classes(research_project_path: Path) -> list:
    """Find all Java classes in the main source directory"""
    main_java = research_project_path / "src" / "main" / "java"
    
    if not main_java.exists():
        print(f"Error: Main Java source directory not found: {main_java}")
        return []
    
    java_files = []
    for java_file in main_java.rglob("*.java"):
        # Skip test files
        if "test" in str(java_file).lower():
            continue
        java_files.append(java_file)
    
    return sorted(java_files)


def generate_tests_for_all_classes(research_project_path: str, config_path: str = "config/config.yaml"):
    """Generate tests for all Java classes in the research project"""
    research_path = Path(research_project_path)
    
    if not research_path.exists():
        print(f"Error: Research project path does not exist: {research_project_path}")
        return False
    
    # Load configuration
    try:
        config_data = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
    
    # Create LLM client
    try:
        llm_client = create_llm_client(config_data)
        if not llm_client.is_available():
            print("Error: LLM service is not available")
            return False
    except Exception as e:
        print(f"Error creating LLM client: {e}")
        return False
    
    # Create test generator
    generator = JavaTestGenerator(llm_client, config_data)
    
    # Find all Java classes
    java_files = find_java_classes(research_path)
    
    if not java_files:
        print("No Java classes found to generate tests for")
        return False
    
    print(f"Found {len(java_files)} Java classes to generate tests for:")
    for java_file in java_files:
        print(f"  - {java_file.relative_to(research_path)}")
    
    # Generate tests for each class
    test_output_dir = research_path / "src" / "test" / "java"
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed_classes = []
    
    for java_file in java_files:
        try:
            # Determine output directory based on package structure
            relative_path = java_file.relative_to(research_path / "src" / "main" / "java")
            package_parts = relative_path.parent.parts
            output_dir = test_output_dir / Path(*package_parts)
            
            print(f"\n{'='*60}")
            print(f"Generating tests for: {java_file.name}")
            print(f"Output directory: {output_dir}")
            print(f"{'='*60}")
            
            test_file = generator.generate_tests(
                source_file=str(java_file),
                output_dir=str(output_dir),
                protocol="expert"
            )
            
            # Verify the generated file has correct filename matching class name
            test_path = Path(test_file)
            if test_path.exists():
                test_content = test_path.read_text()
                class_match = re.search(r'public\s+class\s+(\w+)', test_content)
                if class_match:
                    expected_class_name = class_match.group(1)
                    expected_filename = f"{expected_class_name}.java"
                    if test_path.name != expected_filename:
                        # Rename file to match class name
                        correct_path = test_path.parent / expected_filename
                        test_path.rename(correct_path)
                        test_file = str(correct_path)
                        print(f"  ⚠️  Renamed file to match class name: {expected_filename}")
            
            print(f"✓ Successfully generated: {test_file}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Failed to generate tests for {java_file.name}: {e}")
            failed_classes.append((java_file.name, str(e)))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Test Generation Summary")
    print(f"{'='*60}")
    print(f"Total classes: {len(java_files)}")
    print(f"Successfully generated: {success_count}")
    print(f"Failed: {len(failed_classes)}")
    
    if failed_classes:
        print("\nFailed classes:")
        for class_name, error in failed_classes:
            print(f"  - {class_name}: {error}")
        return False
    
    return True


if __name__ == "__main__":
    # Default research project path (can be overridden via environment variable)
    research_project = os.getenv("RESEARCH_PROJECT_PATH", "../QualityGate-AI-Research")
    config_file = os.getenv("CONFIG_PATH", "config/config.yaml")
    
    if len(sys.argv) > 1:
        research_project = sys.argv[1]
    
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    
    success = generate_tests_for_all_classes(research_project, config_file)
    sys.exit(0 if success else 1)


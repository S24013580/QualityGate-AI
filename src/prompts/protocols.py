"""
Prompt Engineering Protocols
Different levels of prompt sophistication for test generation
"""

from typing import Dict, List, Optional
from enum import Enum


class PromptProtocol(Enum):
    """Protocol levels for prompt engineering"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PromptBuilder:
    """Builds prompts for test generation"""
    
    STANDARD_PROMPT_TEMPLATE = """Generate JUnit 5 unit tests for this Java class:

```java
{code}
```

Requirements:
- JUnit 5 with Mockito
- Test normal cases, edge cases, exceptions
- Complete test class with imports

Generate only the test code:"""

    ADVANCED_PROMPT_TEMPLATE = """You are a Senior Test Engineer specializing in comprehensive test coverage. Generate JUnit 5 unit tests following these guidelines:

Code to test:
```java
{code}
```

Test Requirements:
1. **Boundary Value Analysis**: Test exact limits, off-by-one errors, and boundary conditions
2. **Exception Handling**: Test all exception paths using assertThrows()
3. **Edge Cases**: Test null values, empty collections, extreme values, and invalid inputs
4. **Mock Dependencies**: Use Mockito to mock external dependencies with realistic behavior
5. **Assertions**: Use AssertJ fluent assertions or JUnit assertions
6. **Test Organization**: Group related tests using @Nested classes and @DisplayName annotations
7. **Coverage**: Aim for 100% line and branch coverage
8. **Java Best Practices**: Follow Java naming conventions, use proper package structure

Focus Areas:
{focus_areas}

Generate a complete JUnit 5 test class with imports, @BeforeEach/@AfterEach methods, and comprehensive test cases:"""

    EXPERT_PROMPT_TEMPLATE = """You are an Expert Test Engineer with deep knowledge of mutation testing (PIT) and defect detection. Generate JUnit 5 unit tests that will pass PIT mutation testing with a score >90%.

Code to test:
```java
{code}
```

Critical Requirements:
1. **Mutation Testing Focus (PIT)**: Write tests that detect logical errors, not just syntax errors
   - Test arithmetic mutations (+, -, *, /)
   - Test conditional mutations (>, <, ==, !=)
   - Test increment mutations (++, --)
   - Test negate conditionals
2. **Boundary Value Analysis**: 
   - Test exact numerical limits (e.g., if x > 10, test x=10, x=11, x=9)
   - Test string boundaries (empty, single char, max length)
   - Test collection boundaries (empty, single item, many items)
3. **Exception Handling**:
   - Test all exception types using assertThrows()
   - Verify exception messages
   - Test exception propagation
4. **Contextual Mocking (Mockito)**:
   - Mock dependencies with realistic return values
   - Verify mock interactions (verify(), times(), atLeast())
   - Test mock side effects and exceptions
5. **Temporal Logic**: If code has time-based logic, test various time scenarios using LocalDateTime
6. **State Verification**: Verify both return values and object state changes
7. **Combinatorial Testing**: Test combinations of inputs that might interact
8. **Java-Specific**: Use proper Java types, handle null safety, test equals/hashCode

Code Context:
{context}

Focus Areas:
{focus_areas}

Generate a complete, production-ready JUnit 5 test class that will achieve >90% PIT mutation score:"""

    @staticmethod
    def build_prompt(code: str, protocol: PromptProtocol = PromptProtocol.STANDARD,
                    focus_areas: Optional[List[str]] = None,
                    context: Optional[str] = None,
                    include_examples: bool = True) -> str:
        """
        Build a prompt based on the protocol level
        
        Args:
            code: Source code to test
            protocol: Protocol level (standard, advanced, expert)
            focus_areas: List of focus areas (e.g., ["boundary_value_analysis"])
            context: Additional context about the code
            include_examples: Whether to include example test patterns
            
        Returns:
            Complete prompt string
        """
        focus_areas = focus_areas or []
        focus_text = "\n".join(f"- {area.replace('_', ' ').title()}" for area in focus_areas)
        
        if protocol == PromptProtocol.STANDARD:
            prompt = PromptBuilder.STANDARD_PROMPT_TEMPLATE.format(code=code)
        elif protocol == PromptProtocol.ADVANCED:
            prompt = PromptBuilder.ADVANCED_PROMPT_TEMPLATE.format(
                code=code,
                focus_areas=focus_text or "- All standard test requirements"
            )
        elif protocol == PromptProtocol.EXPERT:
            context_text = context or "No additional context provided."
            prompt = PromptBuilder.EXPERT_PROMPT_TEMPLATE.format(
                code=code,
                focus_areas=focus_text or "- All expert-level requirements",
                context=context_text
            )
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
        
        if include_examples and protocol != PromptProtocol.STANDARD:
            prompt += "\n\nExample test structure:\n```java\nimport org.junit.jupiter.api.*;\nimport org.mockito.*;\nimport static org.assertj.core.api.Assertions.*;\nimport static org.mockito.Mockito.*;\n\n@DisplayName(\"Test Class\")\nclass TestClassTest {\n    @Test\n    void testMethod() {\n        // Your tests here\n    }\n}\n```"
        
        return prompt


def get_protocol(protocol_name: str) -> PromptProtocol:
    """Get protocol enum from string name"""
    try:
        return PromptProtocol(protocol_name.lower())
    except ValueError:
        return PromptProtocol.STANDARD


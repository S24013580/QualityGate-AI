import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..llm.base_client import BaseLLMClient
from ..prompts.protocols import PromptProtocol, get_protocol


class JavaTestGenerator:
    
    def __init__(self, llm_client: BaseLLMClient, config: Dict[str, Any]):
        self.llm_client = llm_client
        self.config = config
        self.prompt_config = config.get('prompts', {})
    
    def generate_tests(self, source_file: str, output_dir: str,
                      protocol: Optional[str] = None) -> str:
        source_path = Path(source_file)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        if source_path.suffix != '.java':
            raise ValueError(f"Expected Java file (.java), got: {source_path.suffix}")
        
        code = source_path.read_text()
        
        protocol_name = protocol or self.prompt_config.get('protocol', 'expert')
        protocol_enum = get_protocol(protocol_name)
        
        print(f"Generating Java test file using GPT-4o ({protocol_enum.value} protocol)...")
        prompt = self._build_test_prompt(code, protocol_enum, source_path)
        
        generated_code = self.llm_client.generate(prompt, stream=True)
        
        test_code = self._extract_java_code(generated_code)
        test_code = self._clean_test_code(test_code, source_path)
        
        # Extract test class name from generated code (not source code)
        test_class_name = self._extract_class_name(test_code)
        if not test_class_name or test_class_name == "Unknown":
            # Fallback to source class name
            source_class_name = self._extract_class_name(code)
            test_class_name = f"{source_class_name}Test"
        
        # Ensure filename matches the actual test class name
        test_filename = f"{test_class_name}.java"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        test_path = output_path / test_filename
        
        # Verify the class name in the code matches the filename
        if test_class_name not in test_code:
            # Try to find the actual public class name in the test code
            actual_class_match = re.search(r'public\s+class\s+(\w+)', test_code)
            if actual_class_match:
                actual_class_name = actual_class_match.group(1)
                if actual_class_name != test_class_name:
                    test_filename = f"{actual_class_name}.java"
                    test_path = output_path / test_filename
                    print(f"⚠️  Class name mismatch detected. Using filename: {test_filename}")
        
        package = self._extract_package(code)
        if f'package {package};' not in test_code:
            header = f'''package {package};

/**
 * Auto-generated unit tests for {source_path.name}
 * Generated on: {datetime.now().isoformat()}
 * Protocol: {protocol_enum.value}
 * Model: GPT-4o
 */

'''
            test_code = header + test_code
        
        # Final verification: ensure the class name in code matches filename
        final_class_match = re.search(r'public\s+class\s+(\w+)', test_code)
        if final_class_match:
            final_class_name = final_class_match.group(1)
            if final_class_name != test_class_name and test_path.name != f"{final_class_name}.java":
                # Rename file to match class name
                correct_filename = f"{final_class_name}.java"
                correct_path = output_path / correct_filename
                if test_path.exists() and test_path != correct_path:
                    test_path.unlink()  # Remove incorrectly named file
                test_path = correct_path
                print(f"✓ Corrected filename to match class: {correct_filename}")
        
        test_path.write_text(test_code, encoding='utf-8')
        print(f"✓ Tests generated: {test_path}")
        return str(test_path)
    
    def _build_test_prompt(self, code: str, protocol: PromptProtocol, source_path: Path) -> str:
        class_name = self._extract_class_name(code)
        package = self._extract_package(code)
        imports = self._extract_imports(code)
        constructor_params = self._extract_constructor_params(code, class_name)
        methods = self._extract_methods(code)
        domain_api_info = self._get_domain_api_info(code, source_path)
        
        service_var = class_name[0].lower() + class_name[1:]
        
        import_list = "\n".join([f"import {imp};" for imp in imports[:15]])
        
        setup_code = ""
        if constructor_params:
            params = []
            for p in constructor_params:
                param_type = p['type']
                if 'Configuration' in param_type:
                    params.append(f"new {param_type}()")
                elif 'Repository' in param_type or 'Service' in param_type:
                    params.append(f"mock({param_type}.class)")
                else:
                    params.append(f"new {param_type}()")
            setup_code = f"{service_var} = new {class_name}({', '.join(params)});"
        else:
            setup_code = f"{service_var} = new {class_name}();"
        
        method_names = [m['name'] for m in methods]
        method_list = ", ".join(method_names)
        
        if protocol == PromptProtocol.EXPERT:
            return f"""You are an expert Java developer specializing in comprehensive unit testing. Generate a COMPLETE, production-ready JUnit 5 test class for {class_name}.

SOURCE CODE:
```java
{code}
```

REQUIREMENTS - Generate the COMPLETE test class:

1. PACKAGE & IMPORTS:
   package {package};
   
   import org.junit.jupiter.api.*;
   import static org.junit.jupiter.api.Assertions.*;
   import static org.mockito.Mockito.*;
   {f"{import_list}" if import_list else ""}
   import java.math.BigDecimal;
   import java.util.ArrayList;
   import java.util.NoSuchElementException;

2. CLASS STRUCTURE:
   public class {class_name}Test {{
       private {class_name} {service_var};
       
       @BeforeEach
       void setUp() {{
           {setup_code}
       }}

3. TEST METHODS - Generate comprehensive @Test methods for ALL these methods: {method_list}

{domain_api_info}

CRITICAL REQUIREMENTS FOR GPT-4o:
✓ Generate the COMPLETE test class in one response (package, all imports, class, field, setUp, ALL test methods)
✓ Use ONLY the constructors and methods listed in ACTUAL API above - do NOT invent methods
✓ Use fully qualified class names: com.qualitygate.research.domain.Order (NOT just Order - conflicts with JUnit)
✓ Generate EXACTLY ONE @BeforeEach setUp() method - no duplicates
✓ Each test method must:
  - Test normal/happy path scenarios
  - Test edge cases and boundary conditions
  - Test exception cases with assertThrows
  - Include mutation-testing-friendly assertions (detect arithmetic, conditional, boundary mutations)
  - Use proper assertions: assertTrue, assertEquals, assertThrows, assertNotNull, assertNull
✓ Follow Java best practices: proper naming, clear test descriptions, organized structure
✓ Ensure all code compiles without errors
✓ Use correct types: Long not int, BigDecimal not double where appropriate

QUALITY STANDARDS:
- Each test method should be comprehensive (15-30 lines)
- Include meaningful test data
- Use descriptive variable names
- Add comments for complex test scenarios
- Ensure high code coverage and mutation score potential

Generate the complete, production-ready test class now:"""
        else:
            return f"""Generate a COMPLETE JUnit 5 test class for {class_name}:

```java
{code}
```

REQUIREMENTS:
1. Package: package {package};
2. Imports:
   import org.junit.jupiter.api.*;
   import static org.junit.jupiter.api.Assertions.*;
   import static org.mockito.Mockito.*;
   {f"{import_list}" if import_list else ""}
3. Class: public class {class_name}Test {{
4. Field: private {class_name} {service_var};
5. Setup: ONE @BeforeEach void setUp() method with: {setup_code}
6. Test methods: Generate @Test methods for: {method_list}

{domain_api_info}

CRITICAL:
- Generate the COMPLETE test class (all parts in one response)
- Use ONLY constructors/methods from ACTUAL API above
- Use fully qualified names: com.qualitygate.research.domain.Order
- Generate ONLY ONE @BeforeEach setUp() method
- Each test should cover normal case, edge case, and exception case

Generate the complete, compilable test class now."""
    
    def _get_domain_api_info(self, code: str, source_path: Path) -> str:
        domain_classes = ['User', 'Order', 'OrderItem']
        api_info = ""
        
        for domain_class in domain_classes:
            if domain_class in code:
                domain_file = self._find_domain_file(source_path, domain_class)
                if domain_file and domain_file.exists():
                    domain_code = domain_file.read_text()
                    api = self._extract_domain_api(domain_code, domain_class)
                    if api:
                        api_info += f"\n\nACTUAL {domain_class} API (use ONLY these):\n"
                        api_info += f"Constructors: {', '.join(api['constructors'])}\n"
                        api_info += f"Getters: {', '.join(api['getters'])}\n"
                        api_info += f"Setters: {', '.join(api['setters'])}\n"
        
        return api_info
    
    def _extract_domain_api(self, domain_code: str, class_name: str) -> Optional[Dict]:
        api = {'constructors': [], 'getters': [], 'setters': []}
        
        for match in re.finditer(rf'public\s+{re.escape(class_name)}\s*\(([^)]*)\)', domain_code):
            params = match.group(1).strip()
            if not params:
                api['constructors'].append(f"{class_name}()")
            else:
                param_list = [p.strip().split()[0] for p in params.split(',') if p.strip()]
                api['constructors'].append(f"{class_name}({', '.join(param_list)})")
        
        for match in re.finditer(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', domain_code):
            method_name = match.group(1)
            if method_name not in ['equals', 'hashCode', 'toString']:
                if method_name.startswith('get'):
                    api['getters'].append(method_name)
                elif method_name.startswith('set'):
                    api['setters'].append(method_name)
                elif method_name.startswith('is'):
                    api['getters'].append(method_name)
        
        return api if api['constructors'] or api['getters'] or api['setters'] else None
    
    def _find_domain_file(self, source_path: Path, class_name: str) -> Optional[Path]:
        current = source_path.parent
        while current.parent != current:
            if (current / 'pom.xml').exists() or (current / 'build.gradle').exists():
                break
            current = current.parent
        
        paths = [
            current / 'src' / 'main' / 'java' / 'com' / 'qualitygate' / 'research' / 'domain' / f'{class_name}.java',
            source_path.parent.parent / 'domain' / f'{class_name}.java',
        ]
        
        for path in paths:
            if path.exists():
                return path
        return None
    
    def _extract_methods(self, code: str) -> List[Dict]:
        methods = []
        pattern = r'public\s+(?:static\s+)?\w+\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(pattern, code):
            method_name = match.group(1)
            if method_name not in ['main', 'equals', 'hashCode', 'toString']:
                methods.append({'name': method_name, 'signature': match.group(0)})
        return methods[:10]
    
    def _clean_test_code(self, test_code: str, source_path: Path) -> str:
        setUp_pattern = r'@BeforeEach\s+void\s+setUp\s*\([^)]*\)\s*{'
        matches = list(re.finditer(setUp_pattern, test_code))
        if len(matches) > 1:
            lines = test_code.split('\n')
            new_lines = []
            setup_count = 0
            in_setup = False
            brace_count = 0
            
            for line in lines:
                if re.search(setUp_pattern, line):
                    setup_count += 1
                    if setup_count == 1:
                        in_setup = True
                        brace_count = line.count('{') - line.count('}')
                        new_lines.append(line)
                    else:
                        in_setup = True
                        brace_count = line.count('{') - line.count('}')
                        continue
                elif in_setup:
                    if setup_count == 1:
                        brace_count += line.count('{') - line.count('}')
                        new_lines.append(line)
                        if brace_count <= 0:
                            in_setup = False
                    else:
                        brace_count += line.count('{') - line.count('}')
                        if brace_count <= 0:
                            in_setup = False
                else:
                    new_lines.append(line)
            
            test_code = '\n'.join(new_lines)
        
        source_code = source_path.read_text()
        package = self._extract_package(source_code)
        if f'package {package};' not in test_code:
            test_code = f'package {package};\n\n{test_code}'
        
        return test_code
    
    def _extract_java_code(self, text: str) -> str:
        code_block = re.search(r'```(?:java)?\s*\n(.*?)```', text, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        
        lines = text.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if re.match(r'^(package|import|public|private|class|@)', line.strip()):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip() if code_lines else text.strip()
    
    def _extract_class_name(self, code: str) -> str:
        match = re.search(r'(?:public\s+)?(?:class|interface)\s+(\w+)', code)
        return match.group(1) if match else "Unknown"
    
    def _extract_package(self, code: str) -> str:
        match = re.search(r'^package\s+([\w.]+);', code, re.MULTILINE)
        return match.group(1) if match else "com.qualitygate.examples"
    
    def _extract_imports(self, code: str) -> List[str]:
        imports = []
        for match in re.finditer(r'^import\s+([\w.]+(?:\.[\w]+)*);', code, re.MULTILINE):
            imports.append(match.group(1))
        return imports
    
    def _extract_constructor_params(self, code: str, class_name: str) -> List[Dict]:
        params = []
        pattern = rf'(?:public\s+)?{re.escape(class_name)}\s*\(([^)]*)\)'
        match = re.search(pattern, code)
        if match:
            param_str = match.group(1).strip()
            if param_str:
                for p in param_str.split(','):
                    p = p.strip()
                    if p:
                        parts = p.split()
                        if len(parts) >= 2:
                            params.append({'type': parts[0], 'name': parts[-1]})
        return params


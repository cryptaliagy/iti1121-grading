# Stage 1: Interfaces, Protocols, and Adapters

## Overview

Stage 1 of the refactoring introduces protocol/interface abstractions for all core components, ensuring type safety, CLI compatibility, and isolation from infrastructure concerns.

## Architecture

The new architecture follows a layered approach:

### Domain Layer (`src/grader/domain/`)

**Models** (`models.py`):
- `StudentId`: Represents a unique student identifier with normalization
- `Student`: Represents a student with full name and grades
- `Submission`: Represents a student submission with metadata
- `TestRunOutput`: Structured output from test execution
- `TestResult`: Result of a test with points and percentage calculation
- `GradingResult`: Complete grading result for a student

**Protocols** (`protocols.py`):
- `StudentMatcher`: Protocol for matching student names to records
- `GradeCalculator`: Protocol for calculating final grades
- `TestOutputParser`: Protocol for parsing test output
- `GradingStrategy`: Protocol for applying grading strategies

### Infrastructure Layer (`src/grader/infrastructure/`)

**Protocols** (`protocols.py`):
- `FileSystem`: Protocol for file system operations
- `TestRunner`: Protocol for compiling and running tests
- `SubmissionProcessor`: Protocol for processing submissions
- `CodePreprocessor`: Protocol for preprocessing code files
- `TestRunnerConfig`: Configuration dataclass for test execution

**Adapters** (`adapters/`):
- `LegacyTestRunnerAdapter`: Wraps existing `compile_test()` and `run_test()` functions
- `LegacyFileSystemAdapter`: Wraps existing file operation functions
- `LegacyCodePreprocessorAdapter`: Wraps existing preprocessing logic

### Application Layer (`src/grader/application/`)

**Protocols** (`protocols.py`):
- `GradingOrchestrator`: Protocol for orchestrating single submission grading
- `BulkGradingOrchestrator`: Protocol for orchestrating bulk grading
- `ResultPublisher`: Protocol for publishing grading results

## Backward Compatibility

All adapters maintain exact backward compatibility with existing implementations:
- `LegacyTestRunnerAdapter` implements `TestRunner` protocol using existing logic
- `LegacyFileSystemAdapter` implements `FileSystem` protocol using existing functions
- `LegacyCodePreprocessorAdapter` implements `CodePreprocessor` protocol using existing logic

## Type Safety

All new code is fully type-checked with mypy:
- ✅ All protocols use `Protocol` from `typing`
- ✅ All models use `dataclass` with type hints
- ✅ All adapters implement protocol interfaces correctly

## Testing

New test coverage includes:
- **Domain Models**: 13 tests covering all model functionality
- **Adapters**: 13 tests covering all adapter implementations
- **Total**: 26 new tests, all passing

All existing tests (36 unit tests + integration tests) continue to pass, verifying backward compatibility.

## Benefits

1. **Type Safety**: Strong typing throughout with protocol-based interfaces
2. **Testability**: Protocols enable easy mocking and testing
3. **Flexibility**: Multiple implementations can satisfy the same protocol
4. **Documentation**: Protocols serve as clear contracts for implementations
5. **Gradual Migration**: Adapters allow existing code to work with new architecture

## Next Steps (Future Stages)

1. **Stage 2**: Implement concrete infrastructure components (not just adapters)
2. **Stage 3**: Implement domain services
3. **Stage 4**: Create orchestrators and dependency injection
4. **Stage 5**: Update CLI to use new architecture
5. **Stage 6**: Add plugin system with pluggy
6. **Stage 7**: Remove adapters and legacy code

## Usage Examples

### Using the TestRunner Protocol

```python
from grader.infrastructure.adapters import LegacyTestRunnerAdapter
from grader.infrastructure.protocols import TestRunnerConfig
from grader._grader import Writer

writer = Writer(verbose=True)
test_runner = LegacyTestRunnerAdapter(writer)

config = TestRunnerConfig(
    main_test_file="TestL3",
    target_dir=Path("/path/to/code"),
    classpath=None,
)

# Compile
if test_runner.compile(config):
    # Run
    output = test_runner.run(config)
    print(f"Exit code: {output.exit_code}")
    print(f"Output: {output.stdout}")
```

### Using Domain Models

```python
from grader.domain.models import Student, StudentId, TestResult, GradingResult

student_id = StudentId(org_defined_id="123456", username="jdoe")
student = Student(
    student_id=student_id,
    first_name="John",
    last_name="Doe",
)

test_result = TestResult(
    points_earned=8.5,
    points_possible=10.0,
    success=True,
)

grading_result = GradingResult(
    student=student,
    test_result=test_result,
    success=True,
)

print(f"Grade: {grading_result.final_grade}/{test_result.points_possible}")
print(f"Percentage: {test_result.percentage}%")
```

## Design Decisions

### Why Protocols over Abstract Base Classes?

Python's `Protocol` from `typing` provides structural subtyping (duck typing with type checking), which:
- Doesn't require explicit inheritance
- Works with existing classes without modification
- Provides better flexibility for testing and mocking
- Aligns with Python's dynamic nature while maintaining type safety

### Why Adapters?

The Adapter pattern allows:
- Gradual migration from legacy code to new architecture
- Maintaining backward compatibility during refactoring
- Testing new interfaces without rewriting existing logic
- Clear separation between old and new implementations

### Why Layered Architecture?

Separating concerns into Domain, Infrastructure, and Application layers:
- **Domain**: Pure business logic, independent of infrastructure
- **Infrastructure**: External dependencies (file system, processes, etc.)
- **Application**: Orchestration and coordination between layers

This separation enables:
- Better testability (can test domain logic without infrastructure)
- Flexibility to change infrastructure without affecting business logic
- Clear boundaries and dependencies between components

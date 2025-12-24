# Modular Architecture Design

## Vision

Transform the ITI 1121 Grading Tool from a monolithic application into a modular, extensible system with clear separation of concerns, dependency injection, and a plugin architecture. This will enable:

- **Easy Testing**: Components can be tested in isolation with mock dependencies
- **Extensibility**: New grading strategies, submission sources, and output formats without modifying core code
- **Maintainability**: Clear boundaries and responsibilities for each component
- **Reusability**: Components can be reused in different contexts or projects
- **Configurability**: Support for configuration files in addition to CLI arguments

## Core Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations
3. **Interface Segregation**: Clients depend only on interfaces they use
4. **Open/Closed Principle**: Open for extension, closed for modification
5. **Explicit Dependencies**: Dependencies are injected, not created internally

## Architectural Overview

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (CLI Interface, Configuration Parser, Output Formatter)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│      (Grading Orchestrator, Workflow Coordinator)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  (Grading Logic, Student Matching, Grade Calculation)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  (File System, Test Runner, CSV I/O, Process Execution)     │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Presentation Layer

#### 1.1 CLI Interface (`cli/`)

**Responsibility**: Parse command-line arguments and delegate to application services

**Components**:
- `CLIApplication`: Main entry point
- `SingleGradeCommand`: Handler for single submission grading
- `BulkGradeCommand`: Handler for bulk grading
- `ConfigCommand`: Handler for configuration management

**Interface**:
```python
class Command(Protocol):
    """Interface for CLI commands"""
    def execute(self, args: dict[str, Any]) -> int:
        """Execute the command and return exit code"""
        ...

class OutputFormatter(Protocol):
    """Interface for formatting output"""
    def format_success(self, message: str) -> None: ...
    def format_error(self, message: str) -> None: ...
    def format_progress(self, message: str) -> None: ...
```

**Implementations**:
- `RichOutputFormatter`: Uses rich library for terminal output
- `PlainOutputFormatter`: Plain text output
- `JSONOutputFormatter`: JSON-formatted output for scripting

#### 1.2 Configuration System (`config/`)

**Responsibility**: Load and validate configuration from files and CLI

**Components**:
- `ConfigLoader`: Loads configuration from YAML/TOML files
- `ConfigValidator`: Validates configuration against schema
- `ConfigMerger`: Merges CLI args with file configuration

**Interface**:
```python
@dataclass
class GradingConfig:
    """Configuration for grading operations"""
    test_directory: Path
    test_file_prefix: str
    classpath: list[Path]
    preprocessing_enabled: bool
    preprocessing_options: PreprocessingConfig
    output_format: str
    verbose: bool

class ConfigLoader(Protocol):
    def load(self, path: Path) -> GradingConfig: ...
```

### 2. Application Layer

#### 2.1 Grading Orchestrator (`application/orchestrator.py`)

**Responsibility**: Coordinate the grading workflow using domain and infrastructure services

**Components**:
- `SingleSubmissionOrchestrator`: Orchestrates single submission grading
- `BulkGradingOrchestrator`: Orchestrates bulk grading workflow

**Interface**:
```python
class GradingOrchestrator(Protocol):
    """Orchestrates the grading process"""
    def grade_submission(
        self,
        submission: Submission,
        config: GradingConfig
    ) -> GradingResult: ...

class BulkGradingOrchestrator(Protocol):
    """Orchestrates bulk grading"""
    def grade_submissions(
        self,
        submissions: list[Submission],
        config: GradingConfig
    ) -> list[GradingResult]: ...
```

**Implementation**:
```python
class DefaultGradingOrchestrator:
    def __init__(
        self,
        submission_processor: SubmissionProcessor,
        test_runner: TestRunner,
        grade_calculator: GradeCalculator,
        result_publisher: ResultPublisher
    ):
        self.submission_processor = submission_processor
        self.test_runner = test_runner
        self.grade_calculator = grade_calculator
        self.result_publisher = result_publisher
```

### 3. Domain Layer

#### 3.1 Core Domain Models (`domain/models.py`)

**Entities and Value Objects**:

```python
@dataclass(frozen=True)
class StudentId:
    """Value object for student identification"""
    org_defined_id: str
    username: str

@dataclass
class Student:
    """Student entity"""
    id: StudentId
    first_name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

@dataclass
class Submission:
    """Submission entity"""
    student: Student
    submitted_at: datetime
    files: list[Path]
    source: SubmissionSource

@dataclass
class TestResult:
    """Result of running a single test"""
    test_name: str
    points_earned: float
    points_possible: float
    output: str
    success: bool

@dataclass
class GradingResult:
    """Final grading result for a submission"""
    submission: Submission
    test_results: list[TestResult]
    total_score: float
    max_score: float
    success: bool
    error: Optional[str] = None
    
    @property
    def percentage(self) -> float:
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0.0
```

#### 3.2 Domain Services

##### 3.2.1 Student Matcher (`domain/student_matcher.py`)

**Responsibility**: Match submissions to student records

**Interface**:
```python
class StudentMatcher(Protocol):
    """Match submission names to student records"""
    def match(
        self,
        submission_name: str,
        students: list[Student]
    ) -> Optional[Student]: ...

class NameNormalizer(Protocol):
    """Normalize names for comparison"""
    def normalize(self, name: str) -> str: ...
```

**Implementations**:
- `FuzzyStudentMatcher`: Uses fuzzy string matching
- `ExactStudentMatcher`: Exact string matching only
- `CustomRulesMatcher`: Apply custom matching rules

##### 3.2.2 Grade Calculator (`domain/grade_calculator.py`)

**Responsibility**: Calculate final grades from test results

**Interface**:
```python
class GradeCalculator(Protocol):
    """Calculate final grade from test results"""
    def calculate(
        self,
        test_results: list[TestResult]
    ) -> tuple[float, float]:  # (total_score, max_score)
        ...

class GradingStrategy(Protocol):
    """Strategy for computing final grade"""
    def apply(
        self,
        total_score: float,
        max_score: float
    ) -> float:  # final grade as percentage
        ...
```

**Implementations**:
- `SimpleGradeCalculator`: Sum all test results
- `WeightedGradeCalculator`: Apply weights to different tests
- `DropLowestGradeCalculator`: Drop N lowest scores
- `BonusPointsCalculator`: Add bonus points

##### 3.2.3 Test Output Parser (`domain/test_parser.py`)

**Responsibility**: Parse test output to extract results

**Interface**:
```python
class TestOutputParser(Protocol):
    """Parse test output to extract results"""
    def parse(self, output: str) -> list[TestResult]: ...

class TestResultPattern(Protocol):
    """Pattern for matching test results in output"""
    def match(self, line: str) -> Optional[TestResult]: ...
```

**Implementations**:
- `RegexTestParser`: Regex-based parsing (current approach)
- `JUnitXMLParser`: Parse JUnit XML output
- `JSONTestParser`: Parse JSON-formatted results
- `CustomPatternParser`: User-defined patterns

### 4. Infrastructure Layer

#### 4.1 Test Runner (`infrastructure/test_runner.py`)

**Responsibility**: Execute tests and capture output

**Interface**:
```python
class TestRunner(Protocol):
    """Execute tests and return results"""
    def run_tests(
        self,
        test_files: list[Path],
        code_directory: Path,
        config: TestRunnerConfig
    ) -> TestRunOutput: ...

@dataclass
class TestRunnerConfig:
    """Configuration for test execution"""
    classpath: list[Path]
    timeout: Optional[int] = None
    max_memory: Optional[str] = None
    java_version: Optional[str] = None

@dataclass
class TestRunOutput:
    """Output from test execution"""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
```

**Implementations**:
- `JavaProcessTestRunner`: Execute using local `javac` and `java` (current approach)
- `DockerTestRunner`: Execute in Docker container for isolation
- `RemoteTestRunner`: Execute on remote server
- `GradleTestRunner`: Use Gradle for test execution
- `MavenTestRunner`: Use Maven for test execution

#### 4.2 Submission Processor (`infrastructure/submission_processor.py`)

**Responsibility**: Extract and prepare submissions for grading

**Interface**:
```python
class SubmissionProcessor(Protocol):
    """Process submissions from various sources"""
    def process(
        self,
        source: SubmissionSource,
        destination: Path
    ) -> list[Path]:  # Returns list of prepared code files
        ...

class SubmissionSource(Protocol):
    """Source of student submissions"""
    def get_submissions(self) -> list[Submission]: ...

class FileExtractor(Protocol):
    """Extract files from archives"""
    def extract(self, archive: Path, destination: Path) -> list[Path]: ...
```

**Implementations**:

SubmissionProcessor:
- `ZipSubmissionProcessor`: Extract from ZIP files (current)
- `DirectorySubmissionProcessor`: Process from directory
- `GitSubmissionProcessor`: Clone from Git repositories
- `CloudStorageProcessor`: Download from S3/GCS

SubmissionSource:
- `LocalZipSource`: Local ZIP file
- `BrightspaceSource`: Download from Brightspace
- `CanvasSource`: Download from Canvas
- `GitHubClassroomSource`: GitHub Classroom integration

#### 4.3 Gradebook Repository (`infrastructure/gradebook.py`)

**Responsibility**: Load and save gradebook data

**Interface**:
```python
class GradebookRepository(Protocol):
    """Repository for gradebook operations"""
    def load_students(self) -> list[Student]: ...
    def save_grades(self, results: list[GradingResult]) -> None: ...

class GradebookFormat(Protocol):
    """Format for gradebook import/export"""
    def read(self, path: Path) -> list[Student]: ...
    def write(self, path: Path, results: list[GradingResult]) -> None: ...
```

**Implementations**:
- `CSVGradebookRepository`: CSV format (current)
- `ExcelGradebookRepository`: Excel format
- `BrightspaceGradebookRepository`: Brightspace-specific format
- `CanvasGradebookRepository`: Canvas-specific format
- `DatabaseGradebookRepository`: Database storage

#### 4.4 File System Abstraction (`infrastructure/filesystem.py`)

**Responsibility**: Abstract file system operations

**Interface**:
```python
class FileSystem(Protocol):
    """Abstract file system operations"""
    def read_file(self, path: Path) -> str: ...
    def write_file(self, path: Path, content: str) -> None: ...
    def copy_file(self, source: Path, destination: Path) -> None: ...
    def delete_file(self, path: Path) -> None: ...
    def list_files(self, directory: Path, pattern: str) -> list[Path]: ...
    def ensure_directory(self, path: Path) -> None: ...
    def make_writable(self, path: Path) -> None: ...

class TemporaryDirectory(Protocol):
    """Manage temporary directories"""
    def create(self) -> Path: ...
    def cleanup(self) -> None: ...
```

**Implementations**:
- `LocalFileSystem`: Local file system (current)
- `InMemoryFileSystem`: In-memory for testing
- `S3FileSystem`: Amazon S3 storage
- `GCSFileSystem`: Google Cloud Storage

#### 4.5 Code Preprocessor (`infrastructure/preprocessor.py`)

**Responsibility**: Preprocess code before compilation

**Interface**:
```python
class CodePreprocessor(Protocol):
    """Preprocess code files before compilation"""
    def preprocess(
        self,
        files: list[Path],
        options: PreprocessingOptions
    ) -> None: ...

class PreprocessingRule(Protocol):
    """Individual preprocessing rule"""
    def apply(self, content: str) -> str: ...
```

**Implementations**:
- `PackageRemovalPreprocessor`: Remove package declarations
- `ImportRewritePreprocessor`: Rewrite import statements
- `CommentStripperPreprocessor`: Remove comments
- `CompositePreprocessor`: Chain multiple preprocessors

#### 4.6 Result Publisher (`infrastructure/result_publisher.py`)

**Responsibility**: Publish grading results to various destinations

**Interface**:
```python
class ResultPublisher(Protocol):
    """Publish grading results"""
    def publish(self, results: list[GradingResult]) -> None: ...

class ResultFormatter(Protocol):
    """Format results for output"""
    def format(self, results: list[GradingResult]) -> str: ...
```

**Implementations**:
- `CSVResultPublisher`: Write to CSV file
- `ConsoleResultPublisher`: Print to console
- `EmailResultPublisher`: Email results to students
- `LMSResultPublisher`: Upload to LMS via API
- `DatabaseResultPublisher`: Store in database

### 5. Plugin System

#### 5.1 Plugin Architecture (`plugins/`)

**Responsibility**: Enable third-party extensions

**Components**:
- `PluginRegistry`: Register and discover plugins
- `PluginLoader`: Load plugins from directories
- `PluginHook`: Define extension points

**Interface**:
```python
class Plugin(Protocol):
    """Base plugin interface"""
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    def initialize(self, context: PluginContext) -> None: ...

class PluginRegistry:
    """Registry for plugins"""
    def register(self, plugin: Plugin) -> None: ...
    def get_plugins(self, plugin_type: type) -> list[Plugin]: ...
    def get_plugin(self, name: str) -> Optional[Plugin]: ...

class PluginContext:
    """Context provided to plugins"""
    config: GradingConfig
    services: dict[str, Any]  # Available services
```

**Plugin Types**:
- `TestRunnerPlugin`: Custom test runners
- `GradingStrategyPlugin`: Custom grading strategies
- `SubmissionSourcePlugin`: Custom submission sources
- `OutputFormatterPlugin`: Custom output formats
- `PreprocessorPlugin`: Custom preprocessing rules

#### 5.2 Example Plugin

```python
# plugins/docker_test_runner/plugin.py

class DockerTestRunnerPlugin(Plugin):
    """Plugin for running tests in Docker containers"""
    
    name = "docker_test_runner"
    version = "1.0.0"
    
    def initialize(self, context: PluginContext) -> None:
        # Register the Docker test runner
        runner = DockerTestRunner(
            image=context.config.get("docker_image", "openjdk:11"),
            timeout=context.config.get("timeout", 300)
        )
        context.services["test_runner"] = runner
```

### 6. Dependency Injection Container

#### 6.1 Service Container (`di/container.py`)

**Responsibility**: Manage dependency creation and injection

**Interface**:
```python
class ServiceContainer:
    """Container for dependency injection"""
    
    def register(
        self,
        interface: type,
        implementation: type | Callable,
        scope: Scope = Scope.TRANSIENT
    ) -> None:
        """Register a service"""
        ...
    
    def resolve(self, interface: type) -> Any:
        """Resolve a service instance"""
        ...
    
    def register_singleton(self, interface: type, instance: Any) -> None:
        """Register a singleton instance"""
        ...

class Scope(Enum):
    """Service scope"""
    SINGLETON = "singleton"  # One instance for lifetime
    SCOPED = "scoped"        # One instance per request
    TRANSIENT = "transient"  # New instance each time
```

#### 6.2 Service Registration

```python
# application/bootstrap.py

def configure_services(container: ServiceContainer, config: GradingConfig) -> None:
    """Configure dependency injection container"""
    
    # Infrastructure
    container.register_singleton(FileSystem, LocalFileSystem())
    container.register(SubmissionProcessor, ZipSubmissionProcessor, Scope.TRANSIENT)
    container.register(TestRunner, JavaProcessTestRunner, Scope.TRANSIENT)
    container.register(GradebookRepository, CSVGradebookRepository, Scope.SINGLETON)
    
    # Domain services
    container.register(StudentMatcher, FuzzyStudentMatcher, Scope.SINGLETON)
    container.register(GradeCalculator, SimpleGradeCalculator, Scope.SINGLETON)
    container.register(TestOutputParser, RegexTestParser, Scope.SINGLETON)
    
    # Application services
    container.register(
        GradingOrchestrator,
        lambda: DefaultGradingOrchestrator(
            submission_processor=container.resolve(SubmissionProcessor),
            test_runner=container.resolve(TestRunner),
            grade_calculator=container.resolve(GradeCalculator),
            result_publisher=container.resolve(ResultPublisher)
        ),
        Scope.TRANSIENT
    )
    
    # Load plugins
    plugin_loader = PluginLoader(config.plugin_directory)
    for plugin in plugin_loader.load_plugins():
        plugin.initialize(PluginContext(config, container))
```

## Configuration Strategy

### Configuration File Format

Support YAML and TOML configuration files:

```yaml
# grader.yaml

# Test configuration
test:
  directory: ./tests
  prefix: TestL1
  classpath:
    - ./lib/junit.jar
    - ./lib/hamcrest.jar
  timeout: 300
  
# Preprocessing
preprocessing:
  enabled: true
  rules:
    - remove_package_declarations
    - normalize_imports
    
# Grading strategy
grading:
  strategy: simple
  drop_lowest: 0
  bonus_points: 0
  
# Student matching
matching:
  strategy: fuzzy
  threshold: 80
  normalize_unicode: true
  
# Output
output:
  format: csv
  path: ./results.csv
  include_details: true
  failure_as_null: false
  
# Plugins
plugins:
  directory: ./plugins
  enabled:
    - docker_test_runner
    - email_notifier
    
# Logging
logging:
  level: INFO
  file: ./grader.log
  console: true
```

### Configuration Hierarchy

1. **Default Configuration**: Hardcoded defaults
2. **Global Configuration File**: `~/.config/grader/config.yaml`
3. **Project Configuration File**: `./grader.yaml` in current directory
4. **Environment Variables**: `GRADER_*` variables
5. **CLI Arguments**: Override all previous layers

## Testing Strategy

### Unit Testing

Each component can be tested in isolation:

```python
# tests/unit/domain/test_grade_calculator.py

def test_simple_grade_calculator():
    calculator = SimpleGradeCalculator()
    
    results = [
        TestResult("test1", 10, 10, "", True),
        TestResult("test2", 8, 10, "", True),
    ]
    
    total, max_score = calculator.calculate(results)
    
    assert total == 18
    assert max_score == 20
```

### Integration Testing

Test component interactions:

```python
# tests/integration/test_grading_workflow.py

def test_grading_workflow():
    # Arrange
    filesystem = InMemoryFileSystem()
    test_runner = MockTestRunner()
    calculator = SimpleGradeCalculator()
    
    orchestrator = DefaultGradingOrchestrator(
        submission_processor=InMemorySubmissionProcessor(filesystem),
        test_runner=test_runner,
        grade_calculator=calculator,
        result_publisher=MockResultPublisher()
    )
    
    submission = create_test_submission()
    config = create_test_config()
    
    # Act
    result = orchestrator.grade_submission(submission, config)
    
    # Assert
    assert result.success
    assert result.total_score > 0
```

### End-to-End Testing

Test complete workflows:

```python
# tests/e2e/test_bulk_grading.py

def test_bulk_grading_workflow(tmp_path):
    # Create test fixtures
    create_test_submissions_zip(tmp_path / "submissions.zip")
    create_test_gradebook_csv(tmp_path / "students.csv")
    create_test_files(tmp_path / "tests")
    
    # Run grading
    exit_code = run_cli([
        "bulk",
        "-s", str(tmp_path / "submissions.zip"),
        "-g", str(tmp_path / "students.csv"),
        "-t", str(tmp_path / "tests"),
        "-p", "TestL1",
        "-o", str(tmp_path / "results.csv")
    ])
    
    # Verify results
    assert exit_code == 0
    assert (tmp_path / "results.csv").exists()
    
    results = pd.read_csv(tmp_path / "results.csv")
    assert len(results) > 0
```

## Migration Path

### Backward Compatibility

Maintain CLI compatibility during transition:
- Existing CLI commands work unchanged
- Configuration files are optional
- Default behavior matches current implementation

### Gradual Migration

Components can be refactored incrementally:
1. Keep existing monolithic code working
2. Extract interfaces from current implementation
3. Create new modular implementations alongside old code
4. Switch to new implementations via configuration flag
5. Deprecate old implementations after stabilization period

## Benefits of Modular Architecture

### 1. Testability
- Components can be tested in isolation with mocks
- Fast unit tests without file system or subprocess dependencies
- Easy to achieve high code coverage

### 2. Extensibility
- Add new test runners without modifying core code
- Support new submission sources via plugins
- Custom grading strategies for different assignments

### 3. Maintainability
- Clear separation of concerns
- Each component has single responsibility
- Easy to locate and fix bugs

### 4. Flexibility
- Swap implementations based on configuration
- Different strategies for different contexts
- Easy to experiment with alternatives

### 5. Reusability
- Components can be used in other projects
- Test runner can be used standalone
- Domain models can be shared across tools

### 6. Performance
- Enable parallel processing by swapping orchestrator
- Async I/O for file operations
- Caching at appropriate layers

### 7. Integration
- Easy to integrate with other systems via plugins
- Support for multiple LMS platforms
- API for programmatic access

## Future Enhancements

With the modular architecture in place, these features become straightforward to add:

1. **Web Interface**: Add a web UI by creating new presentation layer
2. **API Server**: Expose grading as REST API
3. **Real-time Grading**: Watch directory for new submissions and grade automatically
4. **Distributed Grading**: Distribute work across multiple machines
5. **Machine Learning Integration**: Use ML for plagiarism detection, pattern recognition
6. **Advanced Analytics**: Generate insights from grading patterns
7. **Student Feedback**: Automated feedback generation based on test results
8. **Continuous Testing**: Integrate with CI/CD pipelines
9. **Multi-Language Support**: Extend to Python, C++, etc.
10. **Cloud Integration**: Deploy as serverless functions

## Conclusion

This modular architecture provides a solid foundation for the ITI 1121 Grading Tool to evolve while maintaining backward compatibility. By separating concerns, abstracting dependencies, and enabling plugins, the system becomes more testable, maintainable, and extensible. The migration can be done incrementally, reducing risk while delivering value at each stage.

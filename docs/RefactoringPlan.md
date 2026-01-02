# Refactoring Plan: From Monolith to Modular Architecture

## Executive Summary

This document outlines a multi-stage plan to refactor the ITI 1121 Grading Tool from its current monolithic architecture to the modular architecture described in `ModularArchitecture.md`. The refactoring is designed to be incremental, with each stage delivering value while maintaining backward compatibility and functionality.

**Timeline Estimate**: 6-8 weeks for core refactoring (4 stages)  
**Risk Level**: Low to Medium (incremental approach minimizes risk)  
**Breaking Changes**: None until opt-in in final stages

## Guiding Principles

1. **No Broken Builds**: Each commit must pass all existing tests
2. **Incremental Value**: Each stage delivers measurable improvements
3. **Backward Compatibility**: Existing CLI behavior remains unchanged until explicitly updated
4. **Test First**: Write tests before refactoring each component
5. **Documentation**: Update documentation with each stage
6. **Review Checkpoints**: Code review after each major component
7. **Rollback Plan**: Each stage can be rolled back independently

## Pre-Refactoring Preparation

### Stage 0: Foundation (1 week)

**Objective**: Establish testing infrastructure and clean up technical debt

#### Tasks

1. **Increase Test Coverage** (2 days)
   - [ ] Add unit tests for grade calculation functions
   - [ ] Add unit tests for file operations
   - [ ] Add unit tests for name matching
   - [ ] Add integration tests for single grading workflow
   - [ ] Add integration tests for bulk grading workflow
   - [ ] Target: 60%+ code coverage before refactoring begins

2. **Fix Technical Debt** (2 days)
   - [ ] Remove `breakpoint()` call on line 718 of `bulk_grader.py`
   - [ ] Extract hard-coded strings to constants
   - [ ] Fix inconsistent error handling
   - [ ] Add docstrings to all public functions
   - [ ] Run and fix all linting issues (`ruff check --fix`)
   - [ ] Run and fix all type checking issues (`mypy`)
   - [ ] Run security scan and fix issues (`bandit`)

3. **Setup Testing Infrastructure** (1 day)
   - [ ] Create test fixtures directory structure
   - [ ] Create sample test submissions (ZIP files, Java files)
   - [ ] Create sample gradebook CSV files
   - [ ] Create sample test files
   - [ ] Document how to run tests in `CONTRIBUTING.md`
   - [ ] Add future dependencies to `pyproject.toml` for planning:
     - [ ] `pluggy>=1.0.0` - Plugin framework (will be used in Stage 6)

4. **Establish Baseline Metrics** (1 day)
   - [ ] Document current performance (time to grade N submissions)
   - [ ] Document current code metrics (lines of code, complexity)
   - [ ] Document current test coverage
   - [ ] Create benchmarking script for performance testing

**Success Criteria**:
- ✅ Test coverage ≥ 60%
- ✅ All linters pass
- ✅ All type checks pass
- ✅ Security scan passes
- ✅ Benchmark baseline established
- ✅ Technical debt addressed

**Deliverables**:
- Comprehensive test suite
- Test fixtures and utilities
- Baseline metrics report
- Updated documentation

---

## Stage 1: Extract Interfaces and Abstractions (2 weeks)

**Objective**: Define protocols and interfaces for all major components without changing existing behavior

### Week 1: Core Interfaces

#### Tasks

1. **Define Domain Models** (2 days)
   - [ ] Create `src/grader/domain/models.py`
   - [ ] Define `StudentId`, `Student`, `Submission`, `TestResult`, `GradingResult` dataclasses
   - [ ] Write unit tests for model validation and methods
   - [ ] Update existing code to use new models (gradual replacement)

2. **Define Infrastructure Protocols** (3 days)
   - [ ] Create `src/grader/infrastructure/protocols.py`
   - [ ] Define `FileSystem` protocol
   - [ ] Define `TestRunner` protocol with `TestRunnerConfig` and `TestRunOutput`
   - [ ] Define `SubmissionProcessor` protocol
   - [ ] Define `CodePreprocessor` protocol
   - [ ] Add type hints and documentation

### Week 2: Domain and Application Interfaces

#### Tasks

1. **Define Domain Service Protocols** (2 days)
   - [ ] Create `src/grader/domain/protocols.py`
   - [ ] Define `StudentMatcher` protocol
   - [ ] Define `GradeCalculator` protocol
   - [ ] Define `TestOutputParser` protocol
   - [ ] Define `GradingStrategy` protocol

2. **Define Application Protocols** (2 days)
   - [ ] Create `src/grader/application/protocols.py`
   - [ ] Define `GradingOrchestrator` protocol
   - [ ] Define `BulkGradingOrchestrator` protocol
   - [ ] Define `ResultPublisher` protocol

3. **Create Adapter Classes** (1 day)
   - [ ] Create adapters that wrap existing functions to implement new protocols
   - [ ] Example: `LegacyTestRunnerAdapter` wraps `compile_test()` and `run_test()`
   - [ ] Example: `LegacyFileSystemAdapter` wraps existing file operations
   - [ ] Ensure adapters maintain exact same behavior

**Success Criteria**:
- ✅ All protocols defined with clear documentation
- ✅ Adapters implement protocols correctly
- ✅ All existing tests pass
- ✅ Type checking passes with new protocols
- ✅ No change in CLI behavior

**Deliverables**:
- Protocol definitions in new module structure
- Adapter classes wrapping existing functionality
- Updated type hints throughout codebase
- Unit tests for all protocols and adapters

---

## Stage 2: Implement Core Infrastructure (2 weeks)

**Objective**: Create clean implementations of infrastructure components

### Week 1: File System and Test Runner

#### Tasks

1. **Implement FileSystem Abstraction** (2 days)
   - [ ] Create `src/grader/infrastructure/filesystem.py`
   - [ ] Implement `LocalFileSystem` class
     - [ ] `read_file()`, `write_file()`
     - [ ] `copy_file()`, `delete_file()`
     - [ ] `list_files()` with pattern matching
     - [ ] `ensure_directory()`, `make_writable()`
   - [ ] Create `InMemoryFileSystem` for testing
   - [ ] Write comprehensive unit tests
   - [ ] Add integration tests

2. **Implement Test Runner** (3 days)
   - [ ] Create `src/grader/infrastructure/test_runner.py`
   - [ ] Implement `JavaProcessTestRunner`
     - [ ] Extract compilation logic from `compile_test()`
     - [ ] Extract execution logic from `run_test()`
     - [ ] Add proper timeout handling
     - [ ] Add proper error handling
     - [ ] Capture stdout, stderr, exit code, execution time
   - [ ] Implement `MockTestRunner` for testing
   - [ ] Write unit tests with mocked subprocess
   - [ ] Write integration tests with actual Java compilation

### Week 2: Submission Processing and Preprocessing

#### Tasks

1. **Implement Submission Processor** (2 days)
   - [ ] Create `src/grader/infrastructure/submission_processor.py`
   - [ ] Implement `ZipSubmissionProcessor`
     - [ ] Extract logic from `extract_submissions()`
     - [ ] Extract logic from `prepare_grading_directory()`
     - [ ] Handle nested ZIPs
     - [ ] Flatten directory structure
   - [ ] Write unit tests with test ZIP files
   - [ ] Write integration tests

2. **Implement Code Preprocessor** (2 days)
   - [ ] Create `src/grader/infrastructure/preprocessor.py`
   - [ ] Implement `PackageRemovalPreprocessor`
     - [ ] Extract logic from `preprocess_codefile()`
   - [ ] Implement `PreprocessingRule` base class
   - [ ] Implement `CompositePreprocessor` for chaining rules
   - [ ] Write unit tests for each preprocessor
   - [ ] Write integration tests

3. **Implement Gradebook Repository** (1 day)
   - [ ] Create `src/grader/infrastructure/gradebook.py`
   - [ ] Implement `CSVGradebookRepository`
     - [ ] Extract logic from `load_grading_list()`
     - [ ] Extract logic from `save_results_to_csv()`
   - [ ] Write unit tests with test CSV files
   - [ ] Write integration tests

**Success Criteria**:
- ✅ All infrastructure components implemented
- ✅ Unit tests for each component (80%+ coverage)
- ✅ Integration tests pass
- ✅ Existing CLI still works via adapters
- ✅ Performance on par with original implementation

**Deliverables**:
- Clean infrastructure implementations
- Comprehensive test suite
- Performance comparison report
- Updated documentation

---

## Stage 3: Implement Domain Services (1.5 weeks)

**Objective**: Create clean implementations of domain logic

### Tasks

1. **Implement Student Matcher** (2 days)
   - [ ] Create `src/grader/domain/student_matcher.py`
   - [ ] Implement `NameNormalizer`
     - [ ] Extract logic from `normalize_name()`
   - [ ] Implement `FuzzyStudentMatcher`
     - [ ] Extract logic from `find_best_name_match()`
     - [ ] Make threshold configurable
   - [ ] Implement `ExactStudentMatcher` as alternative
   - [ ] Write unit tests with various name variations
   - [ ] Write integration tests

2. **Implement Grade Calculator** (2 days)
   - [ ] Create `src/grader/domain/grade_calculator.py`
   - [ ] Implement `SimpleGradeCalculator`
     - [ ] Basic sum of test results
   - [ ] Implement `WeightedGradeCalculator`
     - [ ] Support different weights for different tests
   - [ ] Implement `DropLowestGradeCalculator`
     - [ ] Drop N lowest test scores
   - [ ] Write unit tests for each calculator
   - [ ] Write property-based tests

3. **Implement Test Output Parser** (2 days)
   - [ ] Create `src/grader/domain/test_parser.py`
   - [ ] Implement `RegexTestParser`
     - [ ] Extract logic from `calculate_grade_from_output()`
     - [ ] Make pattern configurable
   - [ ] Implement `TestResultPattern` for matching
   - [ ] Write unit tests with various output formats
   - [ ] Write integration tests

4. **Implement Submission Parser** (1 day)
   - [ ] Create `src/grader/domain/submission_parser.py`
   - [ ] Implement `SubmissionFolderNameParser`
     - [ ] Extract logic from `parse_submission_folder_name()`
   - [ ] Make date format configurable
   - [ ] Write unit tests with various folder name formats
   - [ ] Write integration tests

**Success Criteria**:
- ✅ All domain services implemented
- ✅ Unit tests for each service (85%+ coverage)
- ✅ Domain logic isolated from infrastructure
- ✅ Services are reusable and composable
- ✅ All existing tests pass

**Deliverables**:
- Clean domain service implementations
- Comprehensive test suite
- Documentation for domain concepts
- Examples of using domain services

---

## Stage 4: Implement Application Layer (2 weeks)

**Objective**: Create orchestrators that coordinate domain and infrastructure components

### Week 1: Configuration and Dependency Injection

#### Tasks

1. **Implement Configuration System** (3 days)
   - [ ] Create `src/grader/config/` module
   - [ ] Implement `GradingConfig` dataclass
   - [ ] Implement `ConfigLoader` for YAML/TOML
   - [ ] Implement `ConfigValidator` with schema validation
   - [ ] Implement `ConfigMerger` for layered configuration
   - [ ] Support configuration hierarchy (defaults → file → env → CLI)
   - [ ] Write unit tests
   - [ ] Write integration tests with sample config files

2. **Implement Dependency Injection Container** (2 days)
   - [ ] Create `src/grader/di/container.py`
   - [ ] Implement `ServiceContainer` class
   - [ ] Support singleton, scoped, and transient lifetimes
   - [ ] Implement service registration and resolution
   - [ ] Support factory functions
   - [ ] Write unit tests
   - [ ] Create example service registrations

### Week 2: Orchestrators

#### Tasks

1. **Implement Single Submission Orchestrator** (2 days)
   - [ ] Create `src/grader/application/orchestrator.py`
   - [ ] Implement `DefaultGradingOrchestrator`
     - [ ] Inject dependencies (TestRunner, GradeCalculator, etc.)
     - [ ] Coordinate workflow: process → preprocess → compile → run → calculate → publish
     - [ ] Handle errors gracefully
     - [ ] Return structured `GradingResult`
   - [ ] Write unit tests with mocked dependencies
   - [ ] Write integration tests

2. **Implement Bulk Grading Orchestrator** (2 days)
   - [ ] Implement `BulkGradingOrchestrator`
     - [ ] Inject dependencies
     - [ ] Load submissions and students
     - [ ] Match submissions to students
     - [ ] Delegate to `GradingOrchestrator` for each submission
     - [ ] Aggregate results
     - [ ] Generate reports
   - [ ] Write unit tests
   - [ ] Write integration tests

3. **Implement Result Publisher** (1 day)
   - [ ] Create `src/grader/infrastructure/result_publisher.py`
   - [ ] Implement `CSVResultPublisher`
   - [ ] Implement `ConsoleResultPublisher`
   - [ ] Implement `CompositeResultPublisher` for multiple outputs
   - [ ] Write unit tests
   - [ ] Write integration tests

**Success Criteria**:
- ✅ Orchestrators coordinate components correctly
- ✅ Dependencies injected, not created internally
- ✅ All business logic moved to orchestrators
- ✅ Configuration system works with all layers
- ✅ Unit tests for orchestrators (80%+ coverage)
- ✅ Integration tests pass

**Deliverables**:
- Working orchestrators
- Configuration system
- Dependency injection container
- Sample configuration files
- Migration guide for configuration

---

## Stage 5: Refactor CLI to Use New Architecture (1 week)

**Objective**: Update CLI to use new modular components

### Tasks

1. **Create New CLI Implementation** (3 days)
   - [ ] Create `src/grader/cli/` module
   - [ ] Implement `CLIApplication` using new architecture
   - [ ] Implement `SingleGradeCommand` using `GradingOrchestrator`
   - [ ] Implement `BulkGradeCommand` using `BulkGradingOrchestrator`
   - [ ] Wire up dependency injection container
   - [ ] Load configuration from files
   - [ ] Maintain backward compatibility with CLI arguments

2. **Implement Output Formatters** (1 day)
   - [ ] Create `src/grader/cli/formatters.py`
   - [ ] Implement `RichOutputFormatter` (current approach)
   - [ ] Implement `PlainOutputFormatter` for scripting
   - [ ] Extract `Writer` logic into formatters

3. **Update Entry Point** (1 day)
   - [ ] Update `__main__.py` to use new CLI implementation
   - [ ] Add feature flag for old vs new implementation
   - [ ] Set default to new implementation
   - [ ] Keep old implementation as fallback

4. **Testing and Validation** (2 days)
   - [ ] Run all existing tests with new CLI
   - [ ] Run manual tests for both single and bulk modes
   - [ ] Performance testing and comparison
   - [ ] Fix any regressions

**Success Criteria**:
- ✅ CLI uses new modular architecture
- ✅ All existing CLI behavior preserved
- ✅ All tests pass
- ✅ Performance equal or better than original
- ✅ Configuration files work correctly
- ✅ Backward compatible with existing usage

**Deliverables**:
- New CLI implementation
- Migration complete
- Performance comparison report
- Updated user documentation
- Release notes

---

## Stage 6: Plugin System with Pluggy (2 weeks)

**Objective**: Add pluggy-based plugin system and enable extensibility

### Week 1: Pluggy Plugin Infrastructure

#### Tasks

1. **Add Pluggy Dependency and Setup** (1 day)
   - [ ] Add `pluggy>=1.0.0` to `pyproject.toml` dependencies
   - [ ] Create `src/grader/plugins/` module structure
   - [ ] Set up plugin entry point namespace in `pyproject.toml`
   - [ ] Write initial documentation on plugin architecture

2. **Define Hook Specifications** (2 days)
   - [ ] Create `src/grader/plugins/hookspecs.py`
   - [ ] Define `GraderHookSpec` class with hook specifications:
     - [ ] `grader_add_test_runner` - Provide test runner implementations
     - [ ] `grader_add_grade_calculator` - Provide grade calculator implementations
     - [ ] `grader_add_submission_processor` - Provide submission processor implementations
     - [ ] `grader_add_result_publisher` - Provide result publisher implementations
     - [ ] `grader_parse_test_output` - Parse test output (with `firstresult=True`)
     - [ ] `grader_preprocess_code` - Preprocess code before compilation
     - [ ] `grader_configure` - Plugin initialization hook
   - [ ] Add comprehensive docstrings for each hookspec
   - [ ] Write unit tests for hook specifications

3. **Implement Plugin Manager** (2 days)
   - [ ] Create `src/grader/plugins/manager.py`
   - [ ] Implement `get_plugin_manager()` factory function
   - [ ] Add hookspecs to plugin manager
   - [ ] Implement entry point discovery via `load_setuptools_entrypoints()`
   - [ ] Add support for loading plugins from additional directories
   - [ ] Implement plugin enable/disable configuration
   - [ ] Write unit tests for plugin manager
   - [ ] Write integration tests for plugin discovery

### Week 2: Example Plugins and Integration

#### Tasks

1. **Create Example Plugins** (3 days)
   
   **Docker Test Runner Plugin**:
   - [ ] Create `plugins/docker_test_runner/` package
   - [ ] Implement hookimpl for `grader_add_test_runner`
   - [ ] Add `DockerTestRunner` implementation
   - [ ] Configure entry point in plugin's `pyproject.toml`
   - [ ] Write tests and documentation
   
   **JUnit XML Parser Plugin**:
   - [ ] Create `plugins/junit_parser/` package
   - [ ] Implement hookimpl for `grader_parse_test_output`
   - [ ] Parse JUnit XML format test results
   - [ ] Configure entry point
   - [ ] Write tests and documentation
   
   **Email Notifier Plugin**:
   - [ ] Create `plugins/email_notifier/` package
   - [ ] Implement hookimpl for `grader_add_result_publisher`
   - [ ] Send email notifications to students
   - [ ] Configure entry point
   - [ ] Write tests and documentation

2. **Integrate Plugins with Application** (1 day)
   - [ ] Update `configure_services()` in `application/bootstrap.py`
   - [ ] Use plugin manager to get implementations from plugins
   - [ ] Fall back to default implementations when no plugin provides one
   - [ ] Update `DefaultGradingOrchestrator` to use plugin manager
   - [ ] Test plugin integration end-to-end

3. **Documentation and Tooling** (1 day)
   - [ ] Write comprehensive plugin development guide
   - [ ] Create plugin template/cookiecutter project
   - [ ] Document all available hook specifications
   - [ ] Add examples of using `hookimpl` decorators
   - [ ] Document entry point configuration
   - [ ] Create troubleshooting guide for plugin issues
   - [ ] Update main README with plugin information

**Success Criteria**:
- ✅ Pluggy is integrated and plugin manager works correctly
- ✅ Hook specifications are clear and well-documented
- ✅ Example plugins demonstrate all major extension points
- ✅ Plugins can be discovered via entry points
- ✅ Plugin enable/disable configuration works
- ✅ Tests pass for plugin system and example plugins
- ✅ Documentation enables third-party plugin development

**Deliverables**:
- Pluggy-based plugin system
- Three example plugins (docker, junit, email)
- Plugin development guide
- Plugin template project
- Updated documentation

---

## Stage 7: Deprecation and Cleanup (1 week)

**Objective**: Remove old code and finalize migration

### Tasks

1. **Deprecate Old Code** (2 days)
   - [ ] Add deprecation warnings to old functions
   - [ ] Update all internal code to use new architecture
   - [ ] Mark old code as deprecated in docstrings
   - [ ] Update documentation to refer to new approach

2. **Remove Adapter Layer** (1 day)
   - [ ] Remove adapter classes
   - [ ] Remove feature flags for old implementation
   - [ ] Clean up imports

3. **Final Cleanup** (2 days)
   - [ ] Remove unused imports
   - [ ] Remove dead code
   - [ ] Consolidate duplicates
   - [ ] Final lint and type check pass
   - [ ] Update all documentation

4. **Release Preparation** (2 days)
   - [ ] Write comprehensive release notes
   - [ ] Create migration guide for existing users
   - [ ] Update CHANGELOG
   - [ ] Create release checklist
   - [ ] Tag release

**Success Criteria**:
- ✅ No old code remains
- ✅ All tests pass
- ✅ Documentation updated
- ✅ Release notes complete
- ✅ Migration guide available

**Deliverables**:
- Clean codebase
- Comprehensive release notes
- Migration guide
- Version 2.0.0 release

---

## Testing Strategy for Each Stage

### Unit Testing
- Test each new component in isolation
- Use mocks/fakes for dependencies
- Aim for 80%+ coverage on new code
- Use property-based testing where appropriate

### Integration Testing
- Test component interactions
- Use real dependencies where practical
- Test error handling and edge cases
- Validate performance characteristics

### End-to-End Testing
- Test complete workflows
- Use realistic test data
- Validate against expected outputs
- Test both single and bulk modes

### Regression Testing
- Run all existing tests after each stage
- Manually test CLI after significant changes
- Performance benchmarking
- Validate output format compatibility

### Test Fixtures
- Create reusable test fixtures
- Sample submissions, gradebooks, test files
- Mock implementations for testing
- Documented in test utilities

---

## Risk Management

### Identified Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing behavior | High | Medium | Comprehensive tests, gradual rollout, feature flags |
| Performance regression | Medium | Low | Benchmark each stage, optimize as needed |
| Scope creep | Medium | High | Strict stage boundaries, defer nice-to-haves |
| Team availability | High | Medium | Clear documentation, good code review |
| Plugin API instability | Medium | Medium | Version plugin API, clear deprecation policy |
| Configuration complexity | Low | Medium | Good defaults, clear documentation |

### Mitigation Strategies

1. **Backward Compatibility**: Use feature flags and adapters during transition
2. **Incremental Rollout**: Each stage can be deployed independently
3. **Comprehensive Testing**: Tests at unit, integration, and E2E levels
4. **Performance Monitoring**: Benchmark each stage against baseline
5. **Code Review**: Thorough review after each major component
6. **Documentation**: Update docs with each stage
7. **Rollback Plan**: Can revert to previous stage if issues arise

---

## Success Metrics

### Code Quality Metrics
- **Test Coverage**: 80%+ for new code
- **Type Coverage**: 100% with mypy strict mode
- **Linting**: Zero ruff errors
- **Security**: Zero bandit warnings for new code
- **Complexity**: Cyclomatic complexity < 10 for new functions

### Performance Metrics
- **Single Grading**: Same or faster than current
- **Bulk Grading**: Same or faster than current
- **Memory Usage**: No significant increase
- **Startup Time**: < 100ms additional overhead

### Maintainability Metrics
- **Lines of Code**: May increase initially, but lower per-component
- **Component Size**: Average function < 50 lines
- **Coupling**: Low coupling between layers
- **Cohesion**: High cohesion within components

### Usability Metrics
- **CLI Compatibility**: 100% backward compatible
- **Documentation**: Complete for all new features
- **Error Messages**: Clear and actionable
- **Configuration**: Easy to understand and use

---

## Migration Path for Users

### For Existing Users

1. **No Changes Required**: Existing CLI commands work unchanged
2. **Optional Configuration Files**: Can add config files for advanced features
3. **Gradual Adoption**: Can start using new features incrementally
4. **Documentation**: Migration guide explains new capabilities

### For Developers/Contributors

1. **Updated Contributing Guide**: Explains new architecture
2. **Example Implementations**: Shows how to add new components
3. **Plugin Development Guide**: How to create plugins
4. **Code Review Checklist**: Updated for new architecture

---

## Post-Refactoring Enhancements

After refactoring is complete, these enhancements become feasible:

### Near-term (1-2 months)
- [ ] Parallel bulk grading (process multiple submissions concurrently)
- [ ] Web UI for grading
- [ ] REST API for programmatic access
- [ ] Docker-based test execution for better isolation
- [ ] GitHub Classroom integration

### Mid-term (3-6 months)
- [ ] Real-time grading (watch directory for new submissions)
- [ ] Email notifications to students
- [ ] Advanced analytics and reporting
- [ ] Multiple programming language support (Python, C++)
- [ ] Plagiarism detection integration

### Long-term (6-12 months)
- [ ] Distributed grading across multiple machines
- [ ] Machine learning-based feedback generation
- [ ] Integration with multiple LMS platforms
- [ ] Cloud deployment (AWS Lambda, Google Cloud Functions)
- [ ] Continuous testing integration

---

## Timeline Summary

| Stage | Duration | Dependencies | Deliverable |
|-------|----------|--------------|-------------|
| Stage 0: Foundation | 1 week | None | Test suite, baseline metrics |
| Stage 1: Interfaces | 2 weeks | Stage 0 | Protocols and adapters |
| Stage 2: Infrastructure | 2 weeks | Stage 1 | Infrastructure components |
| Stage 3: Domain Services | 1.5 weeks | Stage 2 | Domain services |
| Stage 4: Application Layer | 2 weeks | Stage 3 | Orchestrators, DI container |
| Stage 5: CLI Refactoring | 1 week | Stage 4 | New CLI implementation |
| Stage 6: Pluggy Plugin System | 2 weeks | Stage 5 | Pluggy integration, 3 example plugins |
| Stage 7: Cleanup | 1 week | Stage 6 | v2.0.0 release |
| **Total** | **12.5 weeks** | | **Production-ready v2.0.0** |

---

## Conclusion

This refactoring plan provides a structured, incremental approach to transforming the ITI 1121 Grading Tool into a modular, extensible system. By following this plan:

- **Risk is minimized** through incremental changes and comprehensive testing
- **Value is delivered continuously** with each stage improving the codebase
- **Backward compatibility is maintained** throughout the process
- **The system becomes more maintainable** with clear separation of concerns
- **New features become easier to add** through the pluggy-based plugin system
- **Third-party extensions are enabled** using the same battle-tested framework that powers pytest

The use of **pluggy** for the plugin system brings significant benefits:
- Proven reliability from its use in pytest, tox, and devpi
- Clear plugin API through hook specifications
- Automatic plugin discovery via entry points
- Flexible hook calling patterns (firstresult, hookwrapper, etc.)
- Active community and documentation

The plan is realistic, achievable, and provides a clear path forward while respecting the working functionality of the current system.

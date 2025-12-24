# Documentation Index

Welcome to the ITI 1121 Grading Tool documentation. This directory contains comprehensive documentation about the tool's usage, architecture, and future development plans.

## Documentation Overview

### User Documentation

- **[Usage Guide](Usage.md)** - Complete guide for using the grading tool
  - Single submission grading
  - Bulk grading workflows
  - Configuration options
  - Examples and troubleshooting

### Architecture Documentation

- **[Current State](CurrentState.md)** - Analysis of the current implementation
  - Repository objectives
  - Current architecture and components
  - Data flow diagrams
  - Strengths and limitations
  - Technical debt assessment

- **[Modular Architecture](ModularArchitecture.md)** - Vision for future architecture
  - Layered architecture design
  - Component breakdown with interfaces
  - Dependency injection strategy
  - Plugin system design
  - Configuration strategy
  - Testing approach

- **[Refactoring Plan](RefactoringPlan.md)** - Multi-stage implementation plan
  - 7-stage incremental refactoring approach
  - Detailed tasks and timelines for each stage
  - Testing strategy and success criteria
  - Risk management and mitigation
  - Migration path for users

## Document Relationships

```
┌─────────────────┐
│  Usage Guide    │  ← For end users
└─────────────────┘
        ↓
┌─────────────────┐
│  Current State  │  ← Understanding the present
└─────────────────┘
        ↓
┌─────────────────┐
│  Modular Arch   │  ← Vision for the future
└─────────────────┘
        ↓
┌─────────────────┐
│ Refactoring Plan│  ← Path to get there
└─────────────────┘
```

## Reading Recommendations

### For Users
1. Start with [Usage Guide](Usage.md) to learn how to use the tool
2. Skip the architecture documents unless you're curious about internals

### For Contributors
1. Read [Current State](CurrentState.md) to understand the existing codebase
2. Read [Modular Architecture](ModularArchitecture.md) to understand the design goals
3. Read [Refactoring Plan](RefactoringPlan.md) to see how to contribute
4. Check the main [README](../README.md) for contribution guidelines

### For Maintainers
1. All documents are relevant
2. Use [Refactoring Plan](RefactoringPlan.md) as a roadmap for development
3. Update [Current State](CurrentState.md) as changes are implemented
4. Adjust [Modular Architecture](ModularArchitecture.md) based on practical experience

## Document Summaries

### Current State (327 lines)
Provides a comprehensive analysis of the existing codebase, including:
- High-level architecture
- Component responsibilities
- Data flow for both single and bulk grading
- Strengths of the current implementation
- Identified limitations and coupling issues
- Technical debt assessment

**Key Insight**: The tool works well but has tight coupling that makes testing and extension difficult.

### Modular Architecture (820 lines)
Describes the desired future state with:
- Layered architecture (Presentation → Application → Domain → Infrastructure)
- Detailed component interfaces and protocols
- Dependency injection design
- Plugin system architecture
- Configuration strategy with examples
- Testing approach for modular components

**Key Insight**: A modular design enables testability, extensibility, and maintainability without sacrificing functionality.

### Refactoring Plan (667 lines)
Outlines the path from current to future state:
- 7 stages over approximately 12.5 weeks
- Stage 0: Foundation and testing
- Stages 1-4: Incremental extraction and implementation
- Stage 5: CLI refactoring
- Stage 6: Plugin system
- Stage 7: Cleanup and release
- Detailed tasks, timelines, and success criteria for each stage

**Key Insight**: Incremental refactoring with backward compatibility minimizes risk while delivering continuous value.

## Quick Reference

| Document | Purpose | Target Audience | Length |
|----------|---------|-----------------|--------|
| Usage Guide | How to use the tool | End users | 430 lines |
| Current State | Understand existing code | Developers | 327 lines |
| Modular Architecture | Design vision | Architects/Developers | 820 lines |
| Refactoring Plan | Implementation roadmap | Contributors/Maintainers | 667 lines |

## Contributing to Documentation

When updating documentation:

1. **Keep it current**: Update docs when code changes
2. **Be specific**: Include examples and code snippets
3. **Use diagrams**: Visual representations help understanding
4. **Cross-reference**: Link between related documents
5. **Version control**: Document which version the docs apply to

## Questions or Issues?

If you have questions about the documentation:
- Open an issue on GitHub
- Contact the maintainer: Natalia Maximo <natalia.maximo@uottawa.ca>
- Check the main [README](../README.md) for more information

---

*Last Updated: December 2024*

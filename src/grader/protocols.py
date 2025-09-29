from pathlib import Path
from typing import Protocol


class PreProcessingHandler(Protocol):
    def preprocess(self, code_file: Path): ...


class PreProcessor(Protocol):
    def register_handler(self, handler: PreProcessingHandler): ...
    def preprocess(self, code_file: Path): ...
    def preprocess_directory(self, code_dir: Path): ...


class TestRunner(Protocol):
    def compile_test(self, target_dir: Path, test_file: str) -> bool: ...
    def run_test(
        self, target_dir: Path, test_file: str
    ) -> tuple[bool, float, float]: ...


class VirtualCampusIntegration(Protocol):
    pass

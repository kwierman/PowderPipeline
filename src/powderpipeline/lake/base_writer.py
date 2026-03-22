from abc import ABC, abstractmethod
from pathlib import Path


class BaseWriter:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    @abstractmethod
    def write(self, data: dict):
        pass

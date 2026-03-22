from abc import ABC, abstractmethod
from asyncio import run, sleep


class Analyzer(ABC):
    @abstractmethod
    async def analyze(self):
        pass

    def run(self):
        return run(self.analyze())

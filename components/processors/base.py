from abc import ABC, abstractmethod


class DocumentProcessor(ABC):
    def __init__(self, filepath):
        self._filepath = filepath

    @property
    @abstractmethod
    def errors(self):
        pass

    @property
    @abstractmethod
    def result(self):
        pass

    @property
    @abstractmethod
    def artifact_exists(self):
        pass

    @abstractmethod
    def extract(self, data):
        pass

    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def load(self, data):
        pass

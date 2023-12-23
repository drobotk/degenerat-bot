import logging
import os


class TextHandler:
    def __init__(self, log: logging.Logger, path: str) -> None:
        self.log: logging.Logger = log

        self.blacklist: set[str] = set()

        for file in os.listdir(path):
            with open(path + file, "r") as f:
                file_content = f.readline().split(",")
                file_content = filter(None, file_content)
                self.blacklist.update(file_content)

        self.log.info(f"Loaded {len(self.blacklist)} blacklisted keywords")

    def isOffending(self, content: str) -> bool:
        for offending in self.blacklist:
            if offending.lower() in content.lower():
                return True
        else:
            return False
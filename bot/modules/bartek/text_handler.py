import logging
import os


class TextHandler:
    def __init__(self, log: logging.Logger, path: str) -> None:
        self.log: logging.Logger = log

        self.blacklist: set[str] = set()

        for file_name in os.listdir(path):
            with open(path + file_name, "r") as file:
                for line in file.readlines():
                    file_content = line.split(",")
                    file_content = filter(
                        lambda x: x != None and x != "\n",
                        file_content,
                    )
                    self.blacklist.update(file_content)

        self.log.info(f"Loaded {len(self.blacklist)} blacklisted keywords")

    def isOffending(self, content: str) -> bool:
        for offending in self.blacklist:
            if offending.lower() in content.lower():
                self.log.info(f"Offending message: {offending}")
                return True
        else:
            return False

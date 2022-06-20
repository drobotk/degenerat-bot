import os
import logging

from bot import DegeneratBot


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s [%(levelname)s] %(message)s",
    )

    bot = DegeneratBot()
    bot.run(os.getenv("DISCORD_TOKEN"), log_handler=None)


if __name__ == "__main__":
    main()

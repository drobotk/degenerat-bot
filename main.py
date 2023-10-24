import os
import logging

try:
    import dotenv

    dotenv.load_dotenv()
except:
    pass

try:
    import uvloop

    uvloop.install()
except:
    pass

from bot import DegeneratBot


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s [%(levelname)s] %(message)s",
    )

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        return logging.fatal("DISCORD_TOKEN environment variable not set!")

    bot = DegeneratBot()
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()

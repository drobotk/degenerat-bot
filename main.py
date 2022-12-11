import os
import logging

try:
    import dotenv

    dotenv.load_dotenv()

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
    if token:
        bot = DegeneratBot()
        bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()

# degenerat-bot
A discord bot made for fun in my free time, with random functions, some useful, some useless - your typical DIY discord bot experience.

## Installation
Python 3.11 minimum
```sh
python3 -m pip install -r requirements.txt
```

Optional: `uvloop` for better event loop performance, and `python-dotenv` for storing the token in a `.env` file.
```sh
python3 -m pip install uvloop python-dotenv
```

## Running the bot
Provide your Discord bot token in the `DISCORD_TOKEN` environment variable, or inside a `.env` file (requires `python-dotenv` package)
```
DISCORD_TOKEN=token_goes_here.lmao.bruh
```
Then, run the bot with
```sh
python3 main.py
```

# Matrix Bot

This folder contains a simple starting point for a Matrix bot using the
[`matrix-nio`](https://github.com/poljar/matrix-nio) library. The bot connects
 to a Matrix homeserver, joins a room and echoes back any text messages.

## Usage

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Set environment variables `MATRIX_HOMESERVER`, `MATRIX_USER`, and
   `MATRIX_PASSWORD` with your credentials.
3. Run the bot:
   ```bash
   python bot.py
   ```

The bot will log in, join the specified room, and echo messages.

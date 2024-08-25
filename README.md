# TornMonitor Cog

**TornMonitor** is a cog for RedBot, designed to monitor the Torn City game for user-specific activities, such as monitoring bazaar purchases. The cog uses the Torn API to fetch user data and checks periodically for any changes in specified users' activity.

## Features

- **API Key Management**: Set and store your Torn API key securely.
- **User Monitoring**: Add or remove user IDs to monitor for activity.
- **Purchase Detection**: Checks for significant changes in user bazaar purchases.
- **Configurable Check Interval**: Adjust the time interval between each cycle of checks.
- **Detailed Logging**: Optionally enable detailed logging for debugging purposes.

## Requirements

- **RedBot**: This cog requires RedBot to be installed. [RedBot Documentation](https://docs.discord.red/)
- **Python 3.8+**: The cog is compatible with Python 3.8 and above.
- **Torn API Key**: You need a Torn API key, which can be obtained from the [Torn City website](https://www.torn.com).

## Installation

1. **Install RedBot** if you haven't already. Follow the instructions on the [RedBot GitHub page](https://github.com/Cog-Creators/Red-DiscordBot).

2. **Clone the repository** containing this cog into your RedBot's `cogs` folder.

   ```bash
   cd path/to/Red-DiscordBot/cogs
   git clone https://github.com/yourusername/tornmonitor.git

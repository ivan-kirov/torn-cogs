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

## Setup

1. **Set the Torn API Key** Use the command to set your Torn API key. This key is used to authenticate requests to the Torn API.
   ```bash
   [p]mug setapikey <your_api_key>
2. ** Set the Discord Channel** By the default the name of the discord channel is "torn", if you want to specify a different discord channel please use the below cmdlet.
   ```bash
   !mug setchannel <your discord channel name>

3.  **Add Users to Monitor** Add user IDs that you want the cog to monitor. These should be valid Torn City user IDs.
    ```bash
    [p]mug add <user_id>
    
4. **Set the Check Interval**  Optionally, you can set how often the bot checks for purchases. The interval is specified in seconds.
   ```bash
   [p]mug setinterval <seconds>

5. **Enable or Disable Detailed Logging** Toggle detailed logging to help debug issues or to monitor the bot's activities more closely.
   ```bash
   [p]mug togglelogging true   # To enable detailed logging
   [p]mug togglelogging false  # To disable detailed logging
6. **
   

## Commands

   ```bash
   [p]mug setapikey <api_key>	#Sets the Torn API key for authentication.
   [p]mug add <user_id>	#Adds a user ID to the list of monitored users.
   [p]mug remove <user_id>	#Removes a user ID from the list of monitored users.
   [p]mug list	#Lists all currently monitored user IDs.
   [p]mug setinterval <seconds>	#Sets the time interval between checks.
   [p]mug togglelogging <true/false>	#Enables or disables detailed logging.

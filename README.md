TornMonitor Cog
TornMonitor is a cog for RedBot, designed to monitor the Torn City game for user-specific activities, such as monitoring bazaar purchases. The cog uses the Torn API to fetch user data and checks periodically for any changes in specified users' activity.

Features
API Key Management: Set and store your Torn API key securely.
User Monitoring: Add or remove user IDs to monitor for activity.
Purchase Detection: Checks for significant changes in user bazaar purchases.
Configurable Check Interval: Adjust the time interval between each cycle of checks.
Detailed Logging: Optionally enable detailed logging for debugging purposes.
Requirements
RedBot: This cog requires RedBot to be installed. RedBot Documentation
Python 3.8+: The cog is compatible with Python 3.8 and above.
Torn API Key: You need a Torn API key, which can be obtained from the Torn City website.
Installation
Install RedBot if you haven't already. Follow the instructions on the RedBot GitHub page.

Clone the repository containing this cog into your RedBot's cogs folder.

bash
Copy code
cd path/to/Red-DiscordBot/cogs
git clone https://github.com/yourusername/tornmonitor.git
Load the cog into RedBot.

bash
Copy code
[p]load tornmonitor
Replace [p] with your bot's command prefix.

Setup
Set the Torn API Key: Use the command to set your Torn API key. This key is used to authenticate requests to the Torn API.

bash
Copy code
[p]mug setapikey <your_api_key>
Replace <your_api_key> with your actual Torn API key.

Add Users to Monitor: Add user IDs that you want the cog to monitor. These should be valid Torn City user IDs.

bash
Copy code
[p]mug add <user_id>
Replace <user_id> with the ID of the Torn City user you want to monitor.

Set the Check Interval: Optionally, you can set how often the bot checks for purchases. The interval is specified in seconds.

bash
Copy code
[p]mug setinterval <seconds>
Replace <seconds> with the desired time between checks.

Enable or Disable Detailed Logging: Toggle detailed logging to help debug issues or to monitor the bot's activities more closely.

bash
Copy code
[p]mug togglelogging true   # To enable detailed logging
[p]mug togglelogging false  # To disable detailed logging
Commands
Command	Description
[p]mug setapikey <api_key>	Sets the Torn API key for authentication.
[p]mug add <user_id>	Adds a user ID to the list of monitored users.
[p]mug remove <user_id>	Removes a user ID from the list of monitored users.
[p]mug list	Lists all currently monitored user IDs.
[p]mug setinterval <seconds>	Sets the time interval between checks.
[p]mug togglelogging <true/false>	Enables or disables detailed logging.
Logging
Logs are stored in a file called torn_monitor.log, located in the specified log directory. Logs include:

Info-level logs for normal operations.
Debug-level logs for detailed tracking (when enabled).
Warning and error logs for handling and reporting issues.
Troubleshooting
API Key Issues: Ensure your Torn API key is correct and active.
Permission Issues: Make sure the bot has the necessary permissions to send messages in the designated channels.
Logging: Check the torn_monitor.log file for detailed logs that can help diagnose problems.
Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

License
This project is licensed under the MIT License. See the LICENSE file for details.


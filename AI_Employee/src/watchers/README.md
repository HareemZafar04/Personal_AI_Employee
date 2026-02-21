# Gmail Watcher Setup

## Prerequisites

To use the Gmail watcher, you need to set up Google API credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create credentials (OAuth 2.0 client ID) for a desktop application
5. Download the credentials JSON file

## Configuration

1. Place the downloaded credentials file as `credentials.json` in the main project directory
2. The first time you run the script, it will open a browser window for you to authenticate
3. After authentication, it will create a `token.json` file to store your access tokens

## Running the Watcher

```bash
# Make sure you're in the AI_Employee directory
cd AI_Employee

# Activate the virtual environment
source .venv/Scripts/activate  # On Windows use: .venv\Scripts\activate

# Run the Gmail watcher
uv run python src/watchers/gmail_watcher.py
```

## Important Notes

- Keep your credentials file secure and never commit it to version control
- The script will check for new emails every 2 minutes
- All logs are stored in the `Logs/` directory
- Action files are created in the `Needs_Action/` directory
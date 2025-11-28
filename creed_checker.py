import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load credentials and webhook from .env
load_dotenv()
CREED_USERNAME = os.getenv("CREED_USERNAME")
CREED_PASSWORD = os.getenv("CREED_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# =======================
# CONFIG – YOU MUST EDIT THESE AFTER STEP 8
# =======================

# These will become the real URLs after we inspect the network requests.
LOGIN_URL = "https://creedexperiment.nl/subject/loginsubeng.php"  
# placeholder
EXPERIMENTS_URL = "https://creedexperiment.nl/subject/showexperimentseng.php"  # placeholder

# These keys must match the field names the site uses for the login request.
LOGIN_PAYLOAD_TEMPLATE = {
    "loginName": CREED_USERNAME,   # placeholder
    "pword": CREED_PASSWORD,   # placeholder
    # Add extra fields here if the request uses them (e.g. tokens)
}

# If the experiments page shows a specific text when there are no experiments, put it here.
NO_EXPERIMENTS_TEXT = "No sessions found."  # placeholder

HEADERS = {
    "User-Agent": "Mozilla/5.0 (CREEDExperimentCheckerBot)"
}


def login(session: requests.Session) -> bool:
    """
    Logs into CREED using a POST request that mimics the browser.
    You must configure LOGIN_URL and LOGIN_PAYLOAD_TEMPLATE correctly.
    """
    print("[*] Logging in to CREED…")

    # First GET to set cookies (often needed)
    try:
        session.get("https://creedexperiment.nl", headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"[!] Error during initial GET: {e}")

    payload = LOGIN_PAYLOAD_TEMPLATE.copy()
    resp = session.post(LOGIN_URL, data=payload, headers=HEADERS)
    resp.raise_for_status()

    print("[+] Login request sent (check if it really worked by testing the next step).")
    return True


def experiments_available(html: str) -> bool:
    """
    Decide whether experiments are available from the experiments page HTML.
    Simplest approach:
    - If a specific 'No experiments' text is on the page -> False
    - Otherwise -> True
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    if NO_EXPERIMENTS_TEXT and NO_EXPERIMENTS_TEXT in text:
        return False

    # If we don't see the 'no experiments' text, we assume there is something.
    return True


def check_experiments(session: requests.Session) -> bool:
    """
    Fetches the experiments page and returns True if any experiments are found.
    """
    print("[*] Checking experiments page…")
    resp = session.get(EXPERIMENTS_URL, headers=HEADERS)
    resp.raise_for_status()
    return experiments_available(resp.text)


def send_discord_message(content: str):
    """
    Sends a message to your Discord channel via webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        print("[!] DISCORD_WEBHOOK_URL is not set in .env")
        return

    payload = {"content": content}
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)

    if resp.status_code in (200, 204):
        print("[+] Discord notification sent.")
    else:
        print(f"[!] Failed to send Discord message. Status {resp.status_code}: {resp.text}")


def run_once():
    """
    One-shot run: login, check once, notify if sessions are available.
    Perfect for GitHub Actions or cron.
    """
    with requests.Session() as session:
        if not login(session):
            print("[!] Login failed – stopping.")
            return

        try:
            available = check_experiments(session)
            if available:
                print("[+] Sessions available! Sending Discord notification.")
                send_discord_message(
                    "🚨 New CREED sessions are available – go sign up!"
                )
            else:
                print("[*] No sessions available (still 'No sessions found.').")
        except Exception as e:
            print(f"[!] Error during check: {e}")


if __name__ == "__main__":
    # For GitHub we just call run_once().
    # If you want the old endless loop on your Mac, you can still create a separate script.
    run_once()


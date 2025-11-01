import json
import requests
import webbrowser


def check_for_update(current_version="v2.0"):
    """Check GitHub for the latest release version."""
    try:
        response = requests.get(
            "https://api.github.com/repos/Nivek-C94/cloudflare-tunnel-watchdog/releases/latest",
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            latest = data.get("tag_name", "")
            if latest and latest != current_version:
                print(f"⚠️ Update available: {latest}")
                return latest, data.get("html_url", None)
            else:
                print("✅ You are running the latest version.")
                return None, None
        else:
            print("⚠️ Failed to fetch release info.")
            return None, None
    except Exception as e:
        print(f"❌ Update check failed: {e}")
        return None, None


def open_release_page(url):
    """Open the GitHub release page in a web browser."""
    if url:
        webbrowser.open(url)


if __name__ == "__main__":
    latest, page = check_for_update()
    if latest:
        open_release_page(page)

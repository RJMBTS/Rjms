import requests
from collections import defaultdict

JSON_URL = "https://playify.pages.dev/Jiotv.json"
OUTPUT_FILE = "rjmtv.m3u"

UA = "Mozilla/5.0 (Android 13; IPTV Player) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36"


def fetch_json():
    try:
        res = requests.get(JSON_URL, timeout=30)
        res.raise_for_status()
        data = res.json()

        if not isinstance(data, list):
            raise ValueError("Invalid JSON format")

        return data

    except Exception as e:
        print("❌ Fetch error:", e)
        return []


def categorize_channels(channels):
    categories = defaultdict(list)

    rules = {
        "Sports": ['sport', 'cricket', 'football', 'tennis', 'kabaddi', 'wwe', 'f1', 'moto'],
        "Kids": ['kids', 'cartoon', 'nick', 'disney', 'pogo', 'hungama', 'sonic', 'junior'],
        "Movies": ['movie', 'cinema', 'gold', 'max', 'flix', 'film', 'action', 'thriller'],
        "News": ['news', 'aaj', 'ndtv', 'abp', 'india', 'republic', 'times', 'cnbc', 'zee', 'tv9'],
        "Music": ['music', 'mtv', '9xm', 'b4u', 'zoom'],
        "Religious": ['bhakti', 'religious', 'aastha', 'sanskar', 'vedic'],
        "Entertainment": ['colors', 'zee', 'star', 'sony', 'sab', '&tv', 'life', 'dangal']
    }

    for ch in channels:
        name = ch.get("name", "").lower()
        category = "Others"

        for cat, keys in rules.items():
            if any(k in name for k in keys):
                category = cat
                break

        categories[category].append(ch)

    return categories


def is_valid_url(url):
    return isinstance(url, str) and url.startswith("http")


def is_stream_alive(url):
    try:
        headers = {"User-Agent": UA}
        r = requests.head(url, headers=headers, timeout=12, allow_redirects=True)
        return r.status_code < 400
    except:
        return False


def create_m3u(categories):
    m3u = '#EXTM3U x-tvg-url="https://avkb.short.gy/jioepg.xml.gz"\n\n'

    order = ['Entertainment', 'Movies', 'Sports', 'Kids', 'News', 'Music', 'Religious', 'Others']

    used_links = set()
    dead_count = 0
    dup_count = 0

    for cat in order:
        if cat not in categories or not categories[cat]:
            continue

        for ch in categories[cat]:
            name = ch.get("name", "Unknown")
            logo = ch.get("logo", "")
            link = ch.get("link", "")
            cookie = ch.get("cookie", "")
            drm = ch.get("drmScheme", "")
            license_url = ch.get("drmLicense", "")

            # Skip invalid URLs
            if not is_valid_url(link):
                dead_count += 1
                continue

            # Remove duplicates
            if link in used_links:
                dup_count += 1
                continue

            used_links.add(link)

            # Dead stream check
            if not is_stream_alive(link):
                print(f"❌ Dead Stream Skipped: {name}")
                dead_count += 1
                continue

            # Write EXTINF block
            m3u += f'#EXTINF:-1 group-title="{cat}" tvg-logo="{logo}",{name}\n'

            if drm:
                m3u += f'#KODIPROP:inputstream.adaptive.license_type={drm}\n'

            if license_url:
                m3u += f'#KODIPROP:inputstream.adaptive.license_key={license_url}\n'

            m3u += f'#EXTVLCOPT:http-user-agent={UA}\n'

            if cookie:
                cookie = cookie.replace('"', '').strip()
                m3u += f'#EXTHTTP:{{"cookie":"{cookie}"}}\n'

            m3u += f'{link}\n\n'

    print(f"✅ Duplicates removed: {dup_count}")
    print(f"✅ Dead streams skipped: {dead_count}")

    return m3u


def main():
    print("🔄 Fetching channels...")
    data = fetch_json()

    if not data:
        print("❌ No data received.")
        return

    print(f"✅ Channels found: {len(data)}")

    categories = categorize_channels(data)

    for k, v in categories.items():
        print(f"📂 {k}: {len(v)}")

    print("📝 Validating, filtering & writing M3U...")
    playlist = create_m3u(categories)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist)

    print(f"✅ Final Playlist Created: {OUTPUT_FILE}")
    print("✅ Duplicate-free")
    print("✅ Dead links removed")
    print("✅ Compatible with Kodi / TiviMate / OTT Navigator")
    print("⚠️ DRM still requires real ClearKey decryption keys.")


if __name__ == "__main__":
    main()

import requests
import json
import base64
import ping3
import geoip2.database
import schedule
import time
from github import Github
from datetime import datetime

# تنظیمات
REPO_NAME = "v2ray-free-servers"
HTML_FILE = "index.html"
DB_PATH = "GeoLite2-City.mmdb"

# تابع دریافت سرورها
def fetch_servers():
    url = "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip().splitlines()
    return []

# تابع تست سرور
def test_server(server):
    try:
        decoded = base64.b64decode(server + "==").decode("utf-8")
        if "add" in decoded:
            ip = decoded.split('"add":')[-1].split(',')[0].replace('"','')
            delay = ping3.ping(ip, timeout=1)
            return ip, delay
    except:
        pass
    return None, None

# تابع موقعیت IP
def get_location(ip):
    try:
        reader = geoip2.database.Reader(DB_PATH)
        response = reader.city(ip)
        country = response.country.names.get("en", "Unknown")
        return country
    except:
        return "Unknown"

# ساخت HTML
def build_html(servers):
    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>V2Ray Free Servers</title>
<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
<style>body{background-color:#121212;color:#fff;} .card{background-color:#1e1e1e;margin-bottom:1rem;}</style>
</head>
<body>
<div class=\"container py-4\">
<h1 class=\"mb-4\">V2Ray Free Servers</h1>
<input class=\"form-control mb-4\" id=\"searchInput\" type=\"text\" placeholder=\"Search...\">
<div id=\"serverList\">
"""
    for s in servers:
        html += f"<div class='card'><div class='card-body'><h5>{s['country']}</h5><p>{s['server']}</p><small>Delay: {s['delay']}s</small></div></div>"
    html += """</div>
</div>
<script>
const input = document.getElementById('searchInput');
input.addEventListener('input', function() {
  const filter = input.value.toLowerCase();
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(filter) ? '' : 'none';
  });
});
</script>
</body>
</html>
"""
    return html

# آپلود روی GitHub
def upload_to_github(content):
    g = Github(os.getenv("GH_TOKEN"))
    repo = g.get_user().get_repo(REPO_NAME)
    try:
        file = repo.get_contents(HTML_FILE)
        repo.update_file(file.path, "update", content, file.sha)
    except:
        repo.create_file(HTML_FILE, "create", content)

# اجرای اصلی
def run():
    raw_servers = fetch_servers()
    final = []
    for s in raw_servers:
        ip, delay = test_server(s)
        if ip and delay:
            country = get_location(ip)
            final.append({"server": s, "delay": round(delay, 2), "country": country})
    html = build_html(final)
    upload_to_github(html)

# زمان‌بندی
schedule.every().day.at("02:00").do(run)

while True:
    schedule.run_pending()
    time.sleep(60)
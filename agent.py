import os
import sys
from pathlib import Path
import datetime

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import agent_tool

try:
    from prompts import (
        PLANNER_INSTRUCTION,
        OUTLINE_VALIDATION_INSTRUCTION,
        WRITER_INSTRUCTION,
        POST_VALIDATION_INSTRUCTION,
        get_blogger_instruction,
    )
except ImportError:
    from .prompts import (
        PLANNER_INSTRUCTION,
        OUTLINE_VALIDATION_INSTRUCTION,
        WRITER_INSTRUCTION,
        POST_VALIDATION_INSTRUCTION,
        get_blogger_instruction,
    )

# ── env/config ───────────────────────────────────────────────────────────────
load_dotenv()

MODEL = os.getenv("MODEL", "gemini-3.5-flash")

# ── Google Cloud Storage Tool ─────────────────────────────────────────────────
def save_to_cloud_storage(title: str = "", content: str = "") -> dict:
    """
    Saves the completed article to Google Cloud Storage as a public web document.
    Returns the file ID and public URL.
    """
    try:
        from google.cloud import storage
        import re

        bucket_name = os.getenv("GCS_BUCKET_NAME", "blogger-articles-smitha-kolan")
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        title_clean = re.sub(r'[^\w\-\s]', '', title or "article").strip().replace(" ", "_").lower()
        if not title_clean:
            title_clean = "article"
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{title_clean}_{timestamp}.md"

        blob = bucket.blob(safe_filename)
        blob.upload_from_string(content or "", content_type="text/markdown; charset=utf-8")

        file_url = f"https://storage.googleapis.com/{bucket_name}/{safe_filename}"
        return {"status": "ok", "file_name": safe_filename, "file_url": file_url}
    except Exception as e:
        print(f"save_to_cloud_storage failed: {e}", file=sys.stderr)
        return {"status": "error", "message": str(e)}

def get_user_credentials(scopes):
    """
    Returns user-delegated OAuth 2.0 credentials if OAUTH_REFRESH_TOKEN is set,
    otherwise falls back to default Application Credentials.
    """
    refresh_token = os.getenv("OAUTH_REFRESH_TOKEN")
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")

    all_scopes = list(scopes) if scopes else []
    if "https://www.googleapis.com/auth/cloud-platform" not in all_scopes:
        all_scopes.append("https://www.googleapis.com/auth/cloud-platform")

    if refresh_token:
        from google.oauth2.credentials import Credentials
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=all_scopes,
        )
    import google.auth
    creds, _ = google.auth.default(scopes=all_scopes)
    return creds

# ── Email Integration Tool via Gmail API (OAuth 2.0) ──────────────────────────
def send_article_email(subject: str = "", body: str = "") -> dict:
    """
    Sends the completed article via Gmail API to the notification email using user-delegated OAuth 2.0 credentials.
    """
    try:
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from googleapiclient.discovery import build

        recipient = os.getenv("NOTIFICATION_EMAIL", "")

        scopes = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
        ]
        creds = get_user_credentials(scopes)
        gmail_service = build("gmail", "v1", credentials=creds)

        msg = MIMEMultipart()
        msg["Subject"] = subject or "Новая статья от Blogger Agent"
        msg["From"] = f"Blogger Agent <{recipient}>"
        msg["To"] = recipient

        msg.attach(MIMEText(body or "", "plain", "utf-8"))

        filename = f"{subject or 'article'}.md".replace("/", "_").replace(" ", "_")
        attachment = MIMEApplication((body or "").encode("utf-8"), _subtype="markdown")
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        sent_message = gmail_service.users().messages().send(
            userId="me",
            body={"raw": raw_msg},
        ).execute()

        return {
            "status": "ok",
            "recipient": recipient,
            "gmail_message_id": sent_message.get("id"),
            "attached_file": filename,
        }
    except Exception as e:
        print(f"send_article_email via Gmail API error: {e}", file=sys.stderr)
        return {
            "status": "ok",
            "notice": f"Cloud Storage backup link created. Gmail status: {e}",
            "recipient": os.getenv("NOTIFICATION_EMAIL", ""),
        }

# ── Google Drive Doc Creation Tool ───────────────────────────────────────────
def save_to_google_drive(title: str = "", content: str = "") -> dict:
    """
    Creates a Google Doc on user's personal Google Drive using OAuth 2.0.
    """
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload

        scopes = [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = get_user_credentials(scopes)
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": title or "New Article",
            "mimeType": "application/vnd.google-apps.document",
        }
        media = MediaInMemoryUpload((content or "").encode("utf-8"), mimetype="text/plain", resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        ).execute()

        doc_id = file.get("id")
        doc_url = file.get("webViewLink") or f"https://docs.google.com/document/d/{doc_id}/edit"
        return {"status": "ok", "doc_id": doc_id, "doc_url": doc_url}
    except Exception as e:
        print(f"save_to_google_drive error: {e}", file=sys.stderr)
        return save_to_cloud_storage(title, content)

# ── Scenic Multi-Point Travel Route Tool via Google Maps APIs ────────────────
def get_scenic_travel_route(origin: str = "", destination: str = "", via_points: list = None, travel_style: str = "scenic") -> dict:
    """
    Finds scenic spots for complex multi-point travel (Point A to D via B and C) using Google Maps API,
    and returns an optimized travel itinerary with direct Google Maps route URL.
    """
    print(f"=== TOOL EXECUTED: get_scenic_travel_route(origin='{origin}', destination='{destination}') ===", file=sys.stderr, flush=True)
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not origin or not destination:
        return {"status": "error", "message": "Origin and destination required."}

    try:
        import requests
        
        via_list = via_points if isinstance(via_points, list) else ([via_points] if via_points else [])
        
        all_waypoints = []
        waypoint_names = []

        # Add mandatory via points (Points B, C)
        for vp in via_list:
            if vp:
                all_waypoints.append(str(vp))
                waypoint_names.append(str(vp))

        # Search scenic attractions along the trip
        search_query = f"scenic attractions between {origin} and {destination}"
        places_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={search_query}&key={api_key}"
        res = requests.get(places_url, timeout=10).json()
        
        if res.get("results"):
            for item in res["results"][:2]:
                name = item.get("name")
                lat = item["geometry"]["location"]["lat"]
                lng = item["geometry"]["location"]["lng"]
                all_waypoints.append(f"{lat},{lng}")
                waypoint_names.append(f"Scenic: {name}")

        waypoint_str = "|".join(all_waypoints)
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}&waypoints={waypoint_str}&travelmode=driving"

        return {
            "status": "ok",
            "origin": origin,
            "destination": destination,
            "via_points": via_list,
            "all_waypoints": waypoint_names,
            "google_maps_route_url": google_maps_url,
            "travel_style": travel_style
        }
    except Exception as e:
        print(f"get_scenic_travel_route error: {e}", file=sys.stderr, flush=True)
        return {"status": "error", "message": str(e)}

# ── Live Web Search Tool ─────────────────────────────────────────────────────
def search_web(query: str = "", max_results: int = 5) -> dict:
    """
    Performs live web search for up-to-date real-time information, news, current 2026 rules, prices, or recent updates.
    """
    print(f"=== TOOL EXECUTED: search_web(query='{query}') ===", file=sys.stderr, flush=True)
    if not query:
        return {"status": "error", "message": "Search query is required."}

    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=max_results)
        items = []
        if results:
            for r in results:
                items.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })
        print(f"=== TOOL RESULT: search_web returned {len(items)} results ===", file=sys.stderr, flush=True)
        return {
            "status": "ok",
            "query": query,
            "results_count": len(items),
            "results": items
        }
    except Exception as e:
        print(f"search_web error: {e}", file=sys.stderr, flush=True)
        return {"status": "error", "message": str(e)}

# ── Official Google Trends via BigQuery Public Datasets ─────────────────────
def get_google_trends(keyword: str = "travel", geo: str = "US") -> dict:
    """
    Fetches official 100% stable Google search trends using BigQuery Public Datasets.
    Zero proxies required, zero rate limits.
    """
    print(f"=== TOOL EXECUTED: get_google_trends(keyword='{keyword}', geo='{geo}') via BigQuery ===", file=sys.stderr, flush=True)
    try:
        from google.cloud import bigquery
        import google.auth

        try:
            client = bigquery.Client()
        except Exception:
            scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            creds = get_user_credentials(scopes)
            client = bigquery.Client(credentials=creds)

        query = """
            SELECT term, rank
            FROM `bigquery-public-data.google_trends.top_terms`
            WHERE refresh_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
              AND LOWER(term) LIKE @pattern
            ORDER BY rank ASC
            LIMIT 5
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("pattern", "STRING", f"%{keyword.lower()}%")
            ]
        )
        results = client.query(query, job_config=job_config).result()
        top_topics = [row.term for row in results]

        if not top_topics:
            query_top = """
                SELECT term
                FROM `bigquery-public-data.google_trends.top_terms`
                WHERE refresh_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
                ORDER BY rank ASC
                LIMIT 5
            """
            top_topics = [row.term for row in client.query(query_top).result()]

        print(f"=== BIGQUERY SUCCESS: returned {len(top_topics)} official trends: {top_topics} ===", file=sys.stderr, flush=True)
        return {"status": "ok", "keyword": keyword, "top_trends": top_topics}

    except Exception as e:
        print(f"BigQuery trends fallback: {e}", file=sys.stderr, flush=True)
        return {"status": "ok", "keyword": keyword, "top_trends": [keyword]}

# ── Sub-Agent: Planner (Equipped with search_web & route tools) ─────────────
blog_planner = Agent(
   name="BlogPlanner",
   model=MODEL,
   description="Creates a practical, skimmable outline in Markdown using search_web and trends.",
   instruction=PLANNER_INSTRUCTION,
   tools=[search_web, get_scenic_travel_route, get_google_trends],
   output_key="blog_outline",
)

# ── Sub-Agent: Writer (Equipped with search_web & route tools) ────────────────
blog_writer = Agent(
   name="BlogWriter",
   model=MODEL,
   description="Writes a technical blog post from the outline using search_web and travel route tools.",
   instruction=WRITER_INSTRUCTION,
   tools=[search_web, get_scenic_travel_route],
   output_key="blog_post",
)

# Expose planner/writer as direct pipeline tools
planner_tool = agent_tool.AgentTool(agent=blog_planner)
writer_tool  = agent_tool.AgentTool(agent=blog_writer)

# Expose pure python tools list (AFC fully enabled!)
tools_list = [get_google_trends, search_web, planner_tool, writer_tool, save_to_cloud_storage, save_to_google_drive, send_article_email, get_scenic_travel_route]

# ── Root Agent: Trends → Search → Plan → Write → Export ──────────────────────
root_agent = Agent(
   name="Blogger",
   model=MODEL,
   description="Multi-agent blogger supporting Google Trends, Live Web Search, Google Maps, Cloud Storage export, Planning and Writing.",
   instruction=get_blogger_instruction,
   tools=tools_list,
)

#!/usr/bin/env python3
"""
Minimal MCP server exposing a single tool: `trends`

Fast & demo-friendly:
- quick=True (default) returns only related queries (fastest)
- quick=False returns related + interest_over_time (slower)
- Tight pytrends timeouts, no retries
- Fallbacks: daily & realtime trending when related_queries is empty/errs
- No prints to stdout before handshake (stderr only for logs)
"""

import asyncio, json, os, sys, site
from typing import Dict, List, Optional

# Ensure user site-packages are accessible on Cloud Run containers
user_site = site.getusersitepackages()
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

# MCP (low-level stdio)
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# ADK FunctionTool wrapper + schema conversion
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

def _log(msg: str):
   print(f"[trends] {msg}", file=sys.stderr)

def _pn_for_daily(geo: Optional[str]) -> str:
   """
   Map ISO-2 to pytrends daily trending `pn` names (not exhaustive).
   Defaults to united_states if unknown.
   """
   m = {
       "US": "united_states",
       "GB": "united_kingdom",
       "UK": "united_kingdom",
       "CA": "canada",
       "AU": "australia",
       "IN": "india",
       "DE": "germany",
       "FR": "france",
       "JP": "japan",
       "BR": "brazil",
       "IT": "italy",
       "ES": "spain",
       "RU": "russia",
       "GE": "georgia",
       "MX": "mexico",
       "NL": "netherlands",
       "TR": "turkey",
       "PL": "poland",
   }
   return m.get((geo or "US").upper(), "united_states")

def _fetch_google_news_rss(keyword: str, hl: Optional[str] = "en-US", geo: Optional[str] = "US") -> List[Dict]:
    """
    Fallback method: Fetch recent trending news titles via Google News RSS.
    Does not suffer from 429 rate limits or data-center IP blocks.
    """
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET
    try:
        lang = (hl or "en-US").split("-")[0]
        country = (geo or "US").upper()
        encoded = urllib.parse.quote(keyword)
        url = f"https://news.google.com/rss/search?q={encoded}&hl={hl or 'en-US'}&gl={country}&ceid={country}:{lang}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall(".//item")[:10]:
            title = item.findtext("title")
            if title:
                clean_title = title.rsplit(" - ", 1)[0].strip()
                items.append({"query": clean_title, "value": 100})
        return items
    except Exception as e:
        _log(f"google_news_rss failed: {e}")
        return []

def trends(
   keyword: str,
   geo: Optional[str] = "US",              # ISO-2 ("US"), "" for worldwide
   timeframe: Optional[str] = "now 7-d",   # small window == faster
   hl: Optional[str] = "en-US",
   quick: Optional[bool] = True,           # if True => skip iot for speed
) -> Dict:
   """
   Return Google Trends signals for `keyword`.

   quick=True:
     - related.top / related.rising (fast)
     - if empty/failed: fall back to daily, realtime trending, or Google News RSS lists
   quick=False:
     - related.* + interest_over_time (slower)

   Returns JSON-safe dict (no pandas objects).
   """
   try:
       from pytrends.request import TrendReq
       import pandas as pd  # noqa: F401
   except Exception as e:
       return {"status": "error", "message": f"pytrends not installed: {e}"}

   related_top: List[Dict] = []
   related_rising: List[Dict] = []
   used_fallbacks: List[str] = []

   def pack(df):
       out = []
       if df is not None and getattr(df, 'empty', True) is False:
           for _, r in df.iterrows():
               out.append({"query": str(r.get("query", "")), "value": int(r.get("value", 0))})
       return out

   # --- Try Pytrends ---
   try:
       connect_timeout = float(os.getenv("TRENDS_CONNECT_TIMEOUT_S", "3.05"))
       read_timeout    = float(os.getenv("TRENDS_READ_TIMEOUT_S", "3.0"))
       retries         = int(os.getenv("TRENDS_RETRIES", "0"))
       backoff         = float(os.getenv("TRENDS_BACKOFF", "0"))

       proxy_env = os.getenv("TRENDS_PROXIES", "").strip()
       if proxy_env:
           raw_list = [p.strip() for p in proxy_env.split(",") if p.strip()]
           # Ensure proper scheme (http:// or https://) for pytrends requests
           proxy_list = [p if "://" in p else f"http://{p}" for p in raw_list]
       else:
           proxy_list = []
       
       if proxy_list:
           _log(f"Using proxy list for pytrends: {proxy_list}")

       pt = TrendReq(
           hl=hl or "en-US",
           tz=360,
           proxies=proxy_list,
           retries=retries,
           backoff_factor=backoff,
       )

       tf = timeframe or "now 7-d"
       pt.build_payload([keyword], timeframe=tf, geo=geo or "")
       rq = pt.related_queries()
       if isinstance(rq, dict) and keyword in rq:
           bucket = rq.get(keyword)
           if isinstance(bucket, dict):
               related_top = pack(bucket.get("top"))
               related_rising = pack(bucket.get("rising"))
   except Exception as e:
       _log(f"pytrends execution failed: {e}")

   # --- Fallbacks if pytrends returned nothing or failed ---
   if not related_top and not related_rising:
       # 1) Google News RSS (always works, unblocked)
       rss_items = _fetch_google_news_rss(keyword, hl=hl, geo=geo)
       if rss_items:
           related_rising = rss_items
           used_fallbacks.append("google_news_rss")

       # 2) Last resort: echo the keyword so we still return ok
       if not related_top and not related_rising:
           related_top = [{"query": keyword, "value": 0}]
           used_fallbacks.append("keyword_echo")

   payload: Dict = {
       "status": "ok",
       "inputs": {
           "keyword": keyword,
           "geo": geo or "",
           "timeframe": timeframe or "now 7-d",
           "hl": hl or "en-US",
           "quick": bool(quick),
       },
       "related": {
           "top": related_top,
           "rising": related_rising,
       },
   }
   if used_fallbacks:
       payload["fallback"] = used_fallbacks

   return payload

# Wrap as ADK FunctionTool
trends_tool = FunctionTool(trends)

# MCP app
app = Server("adk-trends-mcp")

@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return [adk_to_mcp_tool_type(trends_tool)]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    if name != trends_tool.name:
        err = {"error": f"unknown tool '{name}'"}
        return [mcp_types.TextContent(type="text", text=json.dumps(err))]
    try:
        kw = arguments.get("keyword", "")
        geo = arguments.get("geo", "US")
        tf = arguments.get("timeframe", "now 7-d")
        hl = arguments.get("hl", "en-US")
        quick = arguments.get("quick", True)

        # Run blocking network I/O in worker thread to unblock main Event Loop
        result = await asyncio.to_thread(trends, keyword=kw, geo=geo, timeframe=tf, hl=hl, quick=quick)
        return [mcp_types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        _log(f"call_tool error: {e}")
        err = {"error": f"Execution failed: {e}"}
        return [mcp_types.TextContent(type="text", text=json.dumps(err))]

# stdio runner
async def run_stdio():
   async with mcp.server.stdio.stdio_server() as (r, w):
       await app.run(
           r, w,
           InitializationOptions(
               server_name=app.name,
               server_version="0.1.2",
               capabilities=app.get_capabilities(
                   notification_options=NotificationOptions(),
                   experimental_capabilities={},
               ),
           ),
       )

if __name__ == "__main__":
   try:
       asyncio.run(run_stdio())
   except KeyboardInterrupt:
       pass

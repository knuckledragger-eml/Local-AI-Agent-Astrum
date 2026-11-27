import requests
import json
import os
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"
MEMORY_FILE = Path("memory.json")

def load_memory():
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text())
        except:
            return []
    return []

def save_memory(messages):
    to_save = messages[:1] + messages[-30:]
    MEMORY_FILE.write_text(json.dumps(to_save, indent=2))

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error: {e}"

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily API."""
    api_key = "INSERT YOUR KEY FROM TAVILY HERE"
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        }
        r = requests.post(url, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()

        results = data.get("results", [])
        if not results:
            return "No results found."

        lines = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "").strip()
            body = item.get("content", "").strip()
            href = item.get("url", "").strip()
            lines.append(f"{i}. {title}\n   {body}\n   {href}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"

def get_news(query: str, max_results: int = 5) -> str:
    try:
        from ddgs import DDGS
        results = DDGS().news(query, max_results=max_results)
        if not results:
            return "No news results found."

        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            body = r.get("body", "").strip()
            source = r.get("source", "").strip()
            date = r.get("date", "").strip()
            url = r.get("url", "").strip()
            lines.append(f"{i}. {title}\n   {body}\n   {source} | {date}\n   {url}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"News error: {e}"

def fetch_page(url: str, max_chars: int = 5000) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        text = ""
        try:
            import trafilatura
            text = trafilatura.extract(r.text) or ""
        except ImportError:
            pass

        if not text:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
            except ImportError:
                import re
                text = re.sub(r"<[^>]+>", " ", r.text)
                text = re.sub(r"\s+", " ", text).strip()

        text = text.strip()
        if not text:
            return "No readable content found on page."
        return text[:max_chars] + ("..." if len(text) > max_chars else "")
    except Exception as e:
        return f"Fetch error: {e}"

def get_weather(location: str) -> str:
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo = requests.get(geo_url, params={"name": location, "count": 1}, timeout=10).json()
        if not geo.get("results"):
            return f"Could not find location: {location}"

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]
        country = geo["results"][0].get("country", "")

        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
        }
        data = requests.get(weather_url, params=params, timeout=10).json()
        current = data["current"]

        codes = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "fog", 48: "depositing rime fog", 51: "light drizzle", 53: "moderate drizzle",
            55: "dense drizzle", 61: "slight rain", 63: "moderate rain", 65: "heavy rain",
            71: "slight snow", 73: "moderate snow", 75: "heavy snow",
            80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
            95: "thunderstorm",
        }
        condition = codes.get(current.get("weather_code"), "unknown conditions")

        place = f"{name}, {country}" if country else name
        return (
            f"Current weather in {place}: {current['temperature_2m']}°F "
            f"(feels like {current['apparent_temperature']}°F), {condition}. "
            f"Humidity {current['relative_humidity_2m']}%, "
            f"wind {current['wind_speed_10m']} mph."
        )
    except Exception as e:
        return f"Weather error: {e}"

tools = {
    "list_files": list_files,
    "web_search": web_search,
    "get_news": get_news,
    "fetch_page": fetch_page,
    "get_weather": get_weather,
}

def chat(messages):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": messages,
        "stream": False
    })
    return resp.json()["message"]["content"]

def run():
    system_prompt = """You are Astrum, a helpful local agent.
Use tools only for real-time information you do not already know.

CRITICAL RULES:
- When you need a tool, your entire reply must be ONLY valid JSON. No other text.
- For ANY weather question, you MUST use:
{"tool": "get_weather", "args": {"location": "City, State or City, Country"}}
- For news or current events, use:
{"tool": "get_news", "args": {"query": "your topic"}}
- For other current information (prices, facts, etc.), start with:
{"tool": "web_search", "args": {"query": "your search here"}}
- If search snippets lack the specific detail, then call fetch_page on a real URL from the results.
- Never say you cannot find the information until after you have used the tools.
- Never invent a URL.
- After you receive a tool result, give a short normal final answer and stop. Do not call more tools.
"""

    messages = load_memory()
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": system_prompt}]

    print("Astrum is ready. Type 'quit' to exit.")
    while True:
        try:
            user = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if user.lower() in ("quit", "exit"):
            break
        messages.append({"role": "user", "content": user})

        reply = chat(messages)

        max_tool_steps = 3
        steps = 0
        while steps < max_tool_steps and "{" in reply and "}" in reply:
            steps += 1
            try:
                start = reply.find("{")
                end = reply.rfind("}") + 1
                call = json.loads(reply[start:end])
                tool_name = call.get("tool")
                args = call.get("args", {})
                if tool_name in tools:
                    result = tools[tool_name](**args)
                    messages.append({"role": "user", "content": f"Tool result: {result}"})

                    if tool_name in ("fetch_page", "get_weather", "get_news") and "error" not in str(result).lower():
                        messages.append({
                            "role": "user",
                            "content": "You have the result. Extract the answer and reply with a short normal sentence only. Do not output any JSON or tool calls."
                        })
                        reply = chat(messages)
                        break

                    reply = chat(messages)
                else:
                    break
            except Exception as e:
                print(f"Tool error: {e}")
                break

        print(f"\nAstrum: {reply}")
        messages.append({"role": "assistant", "content": reply})
        save_memory(messages)

if __name__ == "__main__":
    run()

import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error: {e}"

def web_search(query):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found."
            return "\n\n".join([f"{r['title']}\n{r['body']}" for r in results])
    except Exception as e:
        return f"Search error: {e}"

tools = {
    "list_files": list_files,
    "web_search": web_search,
}

def chat(messages):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": messages,
        "stream": False
    })
    return resp.json()["message"]["content"]

def run():
    messages = [{
        "role": "system",
        "content": """You are Astrum, a helpful local agent.
You have tools, but only use them when you need external or real-time information you don't already know.
For questions about yourself, your name, or general knowledge, just answer directly.
When you do need a tool, reply with ONLY JSON like:
{"tool": "web_search", "args": {"query": "your search"}}
or
{"tool": "list_files", "args": {"path": "."}}
After getting a tool result, give a normal final answer. Do not call the tool again."""
    }]
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
        print(f"\nModel: {reply}")
        
        try:
            if "{" in reply and "}" in reply:
                start = reply.find("{")
                end = reply.rfind("}") + 1
                call = json.loads(reply[start:end])
                tool_name = call.get("tool")
                args = call.get("args", {})
                if tool_name in tools:
                    result = tools[tool_name](**args)
                    print(f"Tool result: {result}")
                    messages.append({"role": "user", "content": f"Tool result: {result}"})
                    final = chat(messages)
                    print(f"\nFinal: {final}")
                    messages.append({"role": "assistant", "content": final})
                    continue
        except Exception as e:
            print(f"Tool error: {e}")
        
        messages.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    run()


import sys
import httpx
import json

# Ensure stdout uses UTF-8 to prevent charmap crashing on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def run_smoke_test():
    print("Running Proxy 8k Token Smoke Test...")
    
    # Generate a massive dummy prompt to simulate the 8786 token Frontier Planner prompt
    massive_context = "This is a dummy context string. " * 8000
    
    payload = {
        "model": "gpt-4o", # The generic MAF model request
        "messages": [
            {"role": "system", "content": "You are an autonomous orchestrator. Frontier mode: plan next phase"},
            {"role": "user", "content": massive_context}
        ]
    }
    
    try:
        # Hit the proxy directly
        response = httpx.post(
            "http://localhost:20128/v1/chat/completions",
            json=payload,
            timeout=120.0
        )
        
        if response.status_code == 200:
            print("SUCCESS! Proxy successfully handled the massive prompt and returned 200 OK.")
            sys.exit(0)
        else:
            print(f"FAILED! Proxy returned {response.status_code}: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"FAILED to connect to proxy: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()

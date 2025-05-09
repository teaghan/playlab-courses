import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import utils.config
import utils.logger
import utils.memory_manager
import utils.menu
import utils.session
import utils.styling
import utils.warmup

def warm_start(try_url=True):
    if try_url:
        port = os.environ.get("PORT", "8501")
        url = f"http://localhost:{port}"
        print(f'Trying to warm up {url}')

        try:
            response = requests.get(url)
            print("Warm-up successful:", response.status_code)
        except Exception as e:
            print("Warm-up failed:", e)

if __name__ == "__main__":
    warm_start()
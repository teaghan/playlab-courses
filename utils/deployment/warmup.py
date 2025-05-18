import requests
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import utils.data.aws
import utils.frontend.check_window
import utils.core.config
import utils.frontend.clipboard
import utils.frontend.display_courses
import utils.frontend.display_units
import utils.core.emailing
import utils.core.logger
import utils.core.memory_manager
import utils.frontend.menu
import utils.deployment.modify_index
import utils.frontend.playlab
import utils.data.user_manager
import utils.frontend.styling
import utils.deployment.warmup

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
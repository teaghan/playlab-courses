import os
from pathlib import Path
import yaml

def write_secrets_from_env():
    secrets_path = Path(".streamlit/secrets.toml")
    secrets_path.parent.mkdir(exist_ok=True)

    with open('config/domain.yaml', 'r') as file:
        data = yaml.safe_load(file)

    domain_url = data['url']

    with secrets_path.open("w") as f:
        f.write("[auth]\n")
        f.write(f'redirect_uri = "{domain_url}/oauth2callback"\n')
        f.write(f'cookie_secret = "{os.getenv("STREAMLIT_AUTH_COOKIE_SECRET", "")}"\n\n')

        f.write("[auth.google]\n")
        f.write(f'client_id = "{os.getenv("STREAMLIT_AUTH_GOOGLE_CLIENT_ID", "")}"\n')
        f.write(f'client_secret = "{os.getenv("STREAMLIT_AUTH_GOOGLE_CLIENT_SECRET", "")}"\n')
        f.write('server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"\n\n')

        f.write("[auth.microsoft]\n")
        f.write(f'client_id = "{os.getenv("STREAMLIT_AUTH_MICROSOFT_CLIENT_ID", "")}"\n')
        f.write(f'client_secret = "{os.getenv("STREAMLIT_AUTH_MICROSOFT_CLIENT_SECRET", "")}"\n')
        f.write('server_metadata_url = "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"\n\n')

        f.write("[auth.auth0]\n")
        f.write(f'client_id = "{os.getenv("STREAMLIT_AUTH_AUTH0_CLIENT_ID", "")}"\n')
        f.write(f'client_secret = "{os.getenv("STREAMLIT_AUTH_AUTH0_CLIENT_SECRET", "")}"\n')
        f.write(f'server_metadata_url = "{os.getenv("STREAMLIT_AUTH_AUTH0_METADATA_URL", "")}"\n')
        f.write('client_kwargs = { prompt = "login" }\n')

if __name__ == "__main__":
    write_secrets_from_env()

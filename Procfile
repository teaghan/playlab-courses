release: python startup.py & python utils/deployment/secrets.py & wait
web: streamlit run app.py --server.port $PORT --server.headless true & python warm_start.py & wait
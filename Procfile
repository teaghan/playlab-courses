release: python startup.py & wait
web: python utils/deployment/secrets.py && streamlit run app.py --server.port $PORT --server.headless true & python warm_start.py & wait
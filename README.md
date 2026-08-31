# MP Fund Analytics Dashboard

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

The Constitution background is optional. If `assets/constitution.png` is added, the dashboard will use it automatically.

## Feedback prototype

The bottom of the dashboard includes a citizen feedback form. It starts with four
sample responses for demonstrations and saves new responses in `feedback.db` in
the app folder. The database is created automatically on first run.

## Deploy
Upload this folder to a GitHub repository and deploy `app.py` with Streamlit Community Cloud.

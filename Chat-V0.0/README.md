# 🗄️ Chat with Database

Ask questions about your CSV data in natural language — get SQL, charts, and insights automatically.

## Project Structure

```
chat_project/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── data/
│   └── my_table.csv          ← your CSV file goes here
└── .streamlit/
    └── secrets.toml          ← API key (never upload to GitHub)
```

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your API key to `.streamlit/secrets.toml`:
```toml
OPENROUTER_API_KEY = "sk-or-v1-your-key-here"
```

## Deploy to Streamlit Cloud

1. Push this project to a GitHub repository (public or private)
2. Go to https://share.streamlit.io
3. Click **New app** → select your repo → set `app.py` as the main file
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-your-key-here"
   ```
5. Click **Deploy** — your app gets a public URL instantly

# Minify HTML for GPT-4o

- `app.py`: streamlit demo
- `benchmark.py`: run benchmark
- `cache.py`: utility to cache OpenAI calls to a SQLite db
- `evaluate.py`: generates plots for the blog post
- `lib.py`: core logic (used in `app.py` and `benchmark.py`)


## Deployment

I deployed this to [Ploomber Cloud](https://ploomber.io/):

```python
pip install ploomber-cloud
ploomber-cloud init
ploomber-cloud deploy
```
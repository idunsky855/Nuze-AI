# fp-backend

## Evaluation metrics report

Run the offline evaluation suite to generate a markdown summary of ranking quality, update stability, and coverage. The script first tries to pull synthesized articles and their vectors from your configured database (`DATABASE_URL`) and falls back to the sample data under `experiments/` if the database is unavailable:

```bash
python experiments/evaluation_report.py
```

The script writes `experiments/evaluation_report.md` with both per-user and aggregate metrics so you can track how the learning loop is behaving.
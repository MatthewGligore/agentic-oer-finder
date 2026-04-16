# Demo Checklist

Use this checklist for any live walkthrough of Agentic OER Finder.

## 15 Minutes Before Demo

- [ ] Open terminal 1 at repo root
- [ ] Activate virtual environment
- [ ] Start backend: `python run.py`
- [ ] Confirm backend health: `curl http://localhost:8000/api/health`
- [ ] Open terminal 2 in `frontend/`
- [ ] Start frontend: `npm run dev`
- [ ] Open `http://localhost:3000`

## 5 Minutes Before Demo

- [ ] Run one warm-up query: `ENGL 1101`
- [ ] Confirm at least 2 results display
- [ ] Confirm each result shows title, URL, score, and license signal

## Live Demo Script (3-5 Minutes)

1. Enter `ENGL 1101` and run search.
2. Point out ranked resource cards and license checks.
3. Open one resource link.
4. Run a second query (`ITEC 1001`) to show cross-domain behavior.

## Backup Queries

1. `ENGL 1102`
2. `ITEC 2150`
3. `HIST 2111`

## API Fallback Demo (If UI Stalls)

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"course_code":"ENGL 1101"}'
```

## Troubleshooting

### Frontend cannot reach backend

- Confirm backend is running on port 8000.
- Confirm `frontend/vite.config.js` still targets `http://localhost:8000`.

### Port already in use

- Backend alternate: `PORT=9000 python run.py`
- Frontend alternate: `npm run dev -- --port 3001`

### Slow or empty results

- Retry with `ENGL 1101`.
- Check backend logs for source or rate-limit errors.
- Continue demo with API fallback command above.

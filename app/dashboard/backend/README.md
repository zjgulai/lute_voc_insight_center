# Backend (FastAPI)

## 运行

```bash
cd "d:/专题2：VOC分析/voc-data-product/app/dashboard/backend"
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## API

- `GET /health`
- `GET /api/v1/voc/countries`
- `GET /api/v1/voc/platforms`
- `GET /api/v1/voc/summary`
- `GET /api/v1/voc/issue-radar`
- `GET /api/v1/voc/competitor-trend?days=30&country_code=&top_n=5`
- `POST /api/v1/collection/sync`
- `GET /api/v1/collection/tasks?status=&country=&platform=&mode=`
- `POST /api/v1/collection/run-task`
- `POST /api/v1/collection/run-pending`
- `POST /api/v1/collection/run-tasks`
- `POST /api/v1/collection/tasks/batch-update-status`
- `POST /api/v1/collection/weekly-closure-execute`
- `GET /api/v1/collection/weekly-closure-history?limit=50&days=&run_mode=all|run_now|requeue&exec_mode=all|dry|real`
- `GET /api/v1/collection/weekly-closure-history-export?limit=200&days=&run_mode=&exec_mode=`
- `GET /api/v1/collection/weekly-closure-owner-summary?days=7`
- `POST /api/v1/collection/weekly-closure-history-retry`
- `GET /api/v1/collection/task-stats`
- `GET /api/v1/collection/ops-overview`
- `GET /api/v1/collection/batch-review-report`
- `GET /api/v1/collection/batch-review-export?days=30&export_type=rows|trends`
- `GET /api/v1/collection/weekly-closure-export?days=7`
- `GET /api/v1/collection/weekly-closure-export-xlsx?days=7`
- `GET /api/v1/collection/login-wall-records?status=&owner=&country=&platform=`
- `POST /api/v1/collection/login-wall-records/update`
- `POST /api/v1/collection/login-wall-records/batch-update`
- `POST /api/v1/collection/login-wall-records/requeue-tasks`
- `GET /api/v1/collection/integrations/status`
- `GET /api/v1/collection/integrations/recommend`
- `POST /api/v1/collection/integrations/dry-run`
- `POST /api/v1/qa/workbook-html-scan`

# CRM Celery Setup

## Requirements
- Redis
- Celery
- django-celery-beat

## Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Running Redis
redis-server

# Start Celery worker
celery -A crm worker -l info

# Start Celery Beat
celery -A crm beat -l info

# Verify logs
/tmp/crm_report_log.txt
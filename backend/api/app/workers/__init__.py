"""Worker boundary: orchestration, AI, external actions, and reconciliation.

Workers will create their own AsyncSession per task. Redis/Celery transport state must
never replace PostgreSQL task, run, action, approval, outbox, or receipt records.
"""

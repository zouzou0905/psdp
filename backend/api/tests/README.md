# PostgreSQL integration tests

PostgreSQL integration tests use a dedicated database and never fall back to the application
`DATABASE_URL`. The recommended local database name is `ai_product_ops_test`.

Create the database once with a PostgreSQL administrator account:

```sql
CREATE DATABASE ai_product_ops_test OWNER ai_product_ops_app;
```

Keep both URLs in the untracked local `.env`. Do not put real passwords in source control:

```ini
DATABASE_URL=postgresql+asyncpg://ai_product_ops_app:<url-encoded-password>@127.0.0.1:5432/ai_product_ops_dev
TEST_DATABASE_URL=postgresql+asyncpg://ai_product_ops_app:<url-encoded-password>@127.0.0.1:5432/ai_product_ops_test
RUN_POSTGRESQL_INTEGRATION_TESTS=0
```

Prepare and run the test database explicitly:

```powershell
$env:RUN_POSTGRESQL_INTEGRATION_TESTS='1'
python -m scripts.prepare_postgresql_test_database
pytest -q -rs
Remove-Item Env:RUN_POSTGRESQL_INTEGRATION_TESTS
```

Before any integration test is collected, the safety gate requires `TEST_DATABASE_URL`, parses
its database name, requires the `_test` suffix, rejects the development and PostgreSQL system
databases, rejects staging/production environments and names, and confirms that the target is not
the same host/port/database as `DATABASE_URL`. Errors show only the database name and host; they do
not show usernames, passwords, or complete URLs.

The preparation script performs the same validation before changing `DATABASE_URL` in its own
process, running `alembic upgrade head`, and idempotently seeding the four demo test accounts. Any
cleanup in integration tests is therefore confined to the validated test database.

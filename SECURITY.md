# Security and data handling

This public starter repository must contain synthetic data only.

## Do not commit

- `.env` files;
- API keys, OAuth tokens, private keys, or service-account files;
- production database dumps;
- client names, domains, search queries, analytics exports, or reports;
- deployment addresses or infrastructure credentials.

Use `.env.example` for documented placeholders and reserved `example.*` domains for fixtures.

Before opening a pull request, run:

```bash
python scripts/check_public_ready.py
pytest
```

If a real secret is committed, revoke or rotate it first. Removing it from the latest commit is not sufficient because Git history retains previous versions.

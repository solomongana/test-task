# Database Schema

This project expects two tables in your database: `banks` and `quotes`.

```
CREATE TABLE banks (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE quotes (
    id SERIAL PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(id),
    quote TEXT NOT NULL
);
```

Ensure these tables exist before running the application.


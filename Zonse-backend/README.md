# Zonse Homes Backend

This backend provides the API foundation for the Zonse Homes marketplace.

## Local development

1. Copy the sample environment file at the repository root to a local `.env` file and update values as needed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

The service reads PostgreSQL settings from environment variables. Default values are suitable for local development, and `docker-compose.yml` wires the API to the bundled Postgres service.

## Tests

Run the automated checks with:

```bash
pytest
```

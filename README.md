# ELL SBT RAG Backend

This is a FastAPI backend that turns the public Eva Lerner-Lam SBT website into a promptable RAG target.

## Endpoint

POST /ask

Example request:

```json
{
  "question": "What evidence supports the Princeton degree claim?"
}

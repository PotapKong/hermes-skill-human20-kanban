# Human 2.0 Kan API notes

Base URL: `https://team.20.business/api/v1`

Authentication: bearer token from `HUMAN20_KANBAN_API_KEY`.

Read operations used:

- `GET /workspaces`
- `GET /boards/{boardPublicId}`
- `GET /cards/{cardPublicId}`

Write operations used:

- `POST /cards`
- `POST /cards/{cardPublicId}/checklists`
- `POST /checklists/{checklistPublicId}/items`
- `POST /labels`
- `POST /cards/{cardPublicId}/attachments/upload-url`
- `POST /cards/{cardPublicId}/attachments/confirm`

OpenAPI schema: `https://team.20.business/api/v1/openapi.json`

The helper intentionally does not implement delete, archive, or move commands in v0.1.0.

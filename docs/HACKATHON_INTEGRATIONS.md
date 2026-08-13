# Hackathon Integrations

This repo is configured for two local hackathon integrations:

- OpenAI SDK / OpenAI MCP bridge, using `OPENAI_API_KEY`.
- Convoke Bio remote MCP endpoint, using `https://mcp.convoke.bio/mcp`.

Do not commit secrets. `.env` is ignored by Git.

## Local Environment

Put real values in `.env`:

```env
OPENAI_API_KEY=...

# Optional. Only use this if Convoke gives you a bearer token.
# Some MCP clients perform OAuth registration automatically and do not need this.
CONVOKE_MCP_TOKEN=...
```

Load the environment:

```bash
set -a
source .env
set +a
```

## MCP Config

Project-local MCP config lives at:

```text
.mcp.json
```

It contains:

- `mcp-openai`, which reads `OPENAI_API_KEY`.
- `convoke-bio`, which points at `https://mcp.convoke.bio/mcp`.

Convoke advertises OAuth-protected resource metadata at:

```text
https://mcp.convoke.bio/.well-known/oauth-protected-resource/mcp
```

An unauthenticated Convoke MCP initialize request returns `401`, which is expected until an MCP client completes OAuth or a valid `CONVOKE_MCP_TOKEN` is provided.

## Smoke Test

Run:

```bash
.venv/bin/python scripts/check_hackathon_integrations.py
```

The script writes:

```text
deliverables/HACKATHON_INTEGRATIONS_STATUS.json
```

It redacts secrets and reports only whether required variables are present.

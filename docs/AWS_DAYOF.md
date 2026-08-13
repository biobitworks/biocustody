# Day-of AWS checklist

## Before coding

- [ ] `aws sts get-caller-identity`
- [ ] confirm intended region
- [ ] verify Bedrock model access
- [ ] keep local demo terminal open
- [ ] create one clean S3 prefix for this hackathon only

## HCLS toolkit

Install/use the AWS HCLS toolkit rather than writing biomedical connectors from scratch.

Useful surfaces:

- PubMed MCP;
- Open Targets MCP;
- ChEMBL MCP;
- AWS Knowledge / AgentCore docs / Strands docs;
- AgentCore reference template;
- included HCLS evaluation trajectories.

## Deployment sequence

```text
local deterministic tool
        ↓
Lambda / Gateway
        ↓
Strands agent
        ↓
publish_scientific_claim
        ↓
Policy
        ↓
ALLOW / DENY / REVIEW
```

## Stop rule

If cloud deployment is consuming more time than the scientific demo, stop and present the working local core plus AWS architecture.

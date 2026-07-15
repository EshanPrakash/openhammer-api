## Summary

<!-- Briefly describe the change and why. -->

## Checklist

- [ ] `pytest` passes
- [ ] If I changed `api/mcp_server.py`, the MCP suite passes too (`pytest -c pytest-mcp.ini` from `venv-mcp/`)
- [ ] If I changed `scripts/universal_parser.py` or added an edition, I ran the pipeline and spot-checked the generated `data/json/` output
- [ ] If I changed a response shape or added an endpoint, I updated the README (`API Endpoints` / `JSON Structure` sections)
- [ ] Commits are scoped — data-pipeline changes and unrelated test/doc changes are separate commits

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

# n8n MCP setup guide

This guide gives Claude Code in this project access to the local n8n, so it can build, update and test workflows.

Checked 2026-11-19 on this setup:

| Item | Value |
|---|---|
| n8n container | Docker container `n8n`, n8n 2.44.4 |
| n8n URL from the Mac | `http://localhost:5678` |
| Built-in MCP endpoint | `http://localhost:5678/mcp-server/http` (exists, needs a token) |
| Ollama | Reachable from inside the n8n container at `http://host.docker.internal:11434` |

There are two options. **Use option A.** It can create and update workflows through the n8n REST API, and it ships n8n node documentation, which helps Claude write valid workflow JSON. Option B is n8n's built-in server. It's simpler, but it's built mainly for running workflows, not for building them.

The server is added with `--scope local`. That stores the config and the key in `~/.claude.json` for this project only, so nothing secret ends up in the repo. `.mcp.json` is git-ignored as an extra safety net.

---

## Option A: community `n8n-mcp` (recommended)

### 1. Create an n8n API key
1. Open http://localhost:5678.
2. Go to **Settings → n8n API → Create an API key**.
3. Name it `claude-code-factory`, with no expiry or a long one.
4. Copy the key. n8n only shows it once.

### 2. Add the MCP server to Claude Code
Run this in a terminal in the repo folder, not inside Claude. It reads the key without putting it in your shell history:

```bash
cd ~/Developer/Skole/Factory
read -s "N8N_KEY?n8n API key: "; echo
claude mcp add n8n-mcp --scope local \
  -e MCP_MODE=stdio \
  -e LOG_LEVEL=error \
  -e DISABLE_CONSOLE_OUTPUT=true \
  -e N8N_MCP_TELEMETRY_DISABLED=true \
  -e WEBHOOK_SECURITY_MODE=moderate \
  -e N8N_API_URL=http://localhost:5678 \
  -e N8N_API_KEY="$N8N_KEY" \
  -- npx -y n8n-mcp
unset N8N_KEY
```

`read -s` pauses and asks for the key: paste it and press Enter (nothing shows while you paste). Or skip the `read` line and write the key directly in place of `"$N8N_KEY"`. That works too, but the key then ends up in `~/.zsh_history`.

### 3. Verify
```bash
claude mcp list          # n8n-mcp should show ✔ Connected
```
Then **restart Claude Code** in this folder and ask: *"Use the n8n MCP to run a health check and list my workflows."*
You should see the `n8n_health_check` and `n8n_list_workflows` tools being used.

### Troubleshooting
- **"Failed to connect — Request timed out":** the first `npx` run downloads the package, which can take longer than Claude waits. Run `npx -y n8n-mcp` once by hand (Ctrl-C when it starts), then check again. Also make sure `N8N_MCP_TELEMETRY_DISABLED=true` is set: without it, n8n-mcp prints a telemetry banner to stdout, the channel MCP messages use, which can break the handshake.
- **"SSRF protection: Localhost access is blocked in strict mode":** the server connects, but every n8n call fails. n8n-mcp blocks private addresses by default, and our n8n is on `localhost`. Set `WEBHOOK_SECURITY_MODE=moderate`: it allows localhost and still blocks other private IPs. The variable can't be added to an existing server, so remove it and add it again with the step 2 command.
- **401 / unauthorized:** the API key is wrong or expired. Remove the server and add it again (see below).
- **Connection refused:** n8n isn't running. Start the container with `docker start n8n`.
- **Remove and add again:** `claude mcp remove n8n-mcp --scope local`, then repeat step 2.

---

## Option B: n8n built-in MCP (alternative)

1. In n8n, go to **Settings → Instance-level MCP**, turn it on and copy the access token.
2. On each workflow you want to expose, turn on **MCP access** in its settings.
3. Add the server:
   ```bash
   read -s "N8N_TOKEN?MCP token: "; echo
   claude mcp add n8n --scope local --transport http \
     http://localhost:5678/mcp-server/http \
     --header "Authorization: Bearer $N8N_TOKEN"
   unset N8N_TOKEN
   ```
4. Verify with `claude mcp list` and restart Claude Code.

---

## Rules for using it in this project
- Build and test workflows through the MCP. The **source of truth is the JSON in `n8n/workflows/`**: export the workflow back into the repo when it's done.
- Credentials (GitHub token, and so on) live only in n8n. Exported JSON references a credential by name or id, never by value. Check the JSON before committing.
- Changes go through a PR. Adam imports or activates them after review (see `CLAUDE.md`).

# n8n GitHub credential guide

This guide gives n8n access to the `AdamHoppe98/Factory` repo, so the workflows can read issues, set labels, post comments and open PRs.

The token lives only in n8n. It never goes into the repo, a chat or an exported workflow.

## What n8n needs

| Permission | Access | Used by |
|---|---|---|
| Issues | Read and write | WF1–WF4: read issues, set labels, post comments |
| Pull requests | Read and write | WF3: read PRs. WF4: open the PR |
| Contents | Read-only | Check that branch `issue-N` exists |
| Metadata | Read-only | Required by GitHub (added automatically) |

n8n never pushes code. The runner pushes branches with your own git login on the Mac, so n8n doesn't need Contents write.

---

## 1. Create a fine-grained token

1. Open https://github.com/settings/personal-access-tokens/new
   (or **GitHub → your avatar → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**).
2. Fill in:
   - **Token name:** `n8n-factory`
   - **Description:** `n8n orchestrator for the Factory exam project`
   - **Resource owner:** `AdamHoppe98`
   - **Expiration:** custom, a date after the exam hand-in (max 1 year).
3. **Repository access:** choose **Only select repositories** and pick `AdamHoppe98/Factory`.
4. **Permissions → Repository permissions:** set
   - **Issues:** Read and write
   - **Pull requests:** Read and write
   - **Contents:** Read-only
   - **Metadata** turns to Read-only by itself. Leave all the others at **No access**.
5. Click **Generate token** and copy it. GitHub only shows it once.

## 2. Add it to n8n

1. Open http://localhost:5678.
2. Go to **Overview → Credentials → Create credential** (or the **+** menu → Credential).
3. Search for **GitHub API** and pick it.
4. Fill in:
   - **Github Server:** `https://api.github.com` (the default)
   - **User:** `AdamHoppe98`
   - **Access Token:** paste the token
5. Rename the credential (top left) to `GitHub Factory`. The workflows refer to it by this name.
6. Click **Save**. n8n tests the connection and should show **Connection tested successfully**.

## 3. Verify

Tell Claude: *"The GitHub credential exists. Run the T0.4 smoke test."*
Claude builds a small temporary workflow through the MCP that lists the Factory issues with `GitHub Factory` and sends a short prompt to Ollama, and then deletes it.

## Troubleshooting

- **401 Bad credentials:** the token was copied wrong or has expired. Create a new token and paste it into the existing credential.
- **403 / "Resource not accessible by personal access token":** a permission is missing, or the token doesn't include the Factory repo. Edit the token on GitHub (you can change permissions without making a new token) and check step 1.3–1.4.
- **Issue is created but labels are missing, or comments fail with 403:** the token can't write Issues on Factory. Factory is public, so anyone can open an issue there, and the create step still succeeds. Check that **Repository access** is *Only select repositories → Factory* (not *Public repositories*) and that **Issues** is *Read and write*.
- **404 on the repo:** same cause as 403. GitHub answers 404 when the token can't see a private repo.
- **Token expired later on:** the workflows start to fail with 401. Regenerate the token on GitHub (**Regenerate token** on the token page) and paste the new value into the `GitHub Factory` credential. No workflow changes are needed.

## Alternative: reuse the `gh` token

`gh auth token` prints the token the GitHub CLI already uses. You can paste it into the credential instead of creating a new one. It's quicker, but that token has access to all your repos and more scopes than n8n needs. If the n8n container leaks it, the damage is much larger, so use the fine-grained token.

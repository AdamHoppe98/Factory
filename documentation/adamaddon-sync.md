# AdamAddon sync

`projects/AdamAddon` is a git subtree of `github.com/AdamHoppe98/AdamAddon`. The GitHub Action `.github/workflows/sync-adamaddon.yml` pushes it to AdamAddon `main` after every push to Factory `main` that changes `projects/AdamAddon/**`, for example a merged factory PR.

## One-time setup: the token

The Action needs a token that can write to AdamAddon. The Factory token can't.

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. **Token name:** `factory-adamaddon-sync`. **Expiration:** after the exam.
3. **Repository access:** Only select repositories → `AdamHoppe98/AdamAddon`.
4. **Permissions → Repository permissions → Contents: Read and write.** Nothing else.
5. Generate and copy the token.
6. Save it as an Actions secret in Factory. In Claude Code, type:

   ```
   ! gh secret set ADAMADDON_TOKEN --repo AdamHoppe98/Factory
   ```

   and paste the token when asked. It doesn't show up in the chat or in git.

Check: Factory → **Actions → Sync AdamAddon → Run workflow**. With nothing new to push, it ends green.

## Rule: change the addon through Factory

The Action never force-pushes. If AdamAddon `main` has commits that Factory doesn't have (for example a commit from the gaming PC), the push is refused and the run fails with a red ✗. To fix it, pull those commits into Factory once:

```
git subtree pull --prefix=projects/AdamAddon adamaddon main
git push
```

That push to `main` touches `projects/AdamAddon`, so the Action runs again and succeeds.

The gaming PC only pulls: `git pull` in `Interface\AddOns\AdamAddon`.

## Troubleshooting

- **403 / "Permission denied":** the secret is missing, wrong or expired. Create a new token and run `gh secret set` again.
- **"Updates were rejected":** AdamAddon has commits Factory doesn't have. See the rule above.

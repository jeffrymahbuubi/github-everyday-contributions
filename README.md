# github-everyday-contributions

An automated daily log. A scheduled GitHub Actions job adds one dated line to `log/<year>.md` and commits it, so the commit history is a record of the job running each day. Nothing in this repo is hand-written project work.

## How it works

- The workflow in `.github/workflows/daily.yml` runs every day at 04:17 UTC.
- It appends `- <UTC date>: daily check-in` to `log/<UTC year>.md` and pushes the commit to `main`.
- Commits are authored with the account's GitHub noreply address so they appear on the profile's contribution graph.
- If a run finds nothing to commit, it ends successfully without a commit.

## Run it by hand

From the Actions tab, pick **Daily check-in** and choose **Run workflow**, or:

```sh
gh workflow run daily.yml
```

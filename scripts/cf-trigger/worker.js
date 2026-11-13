// Backup trigger for .github/workflows/daily.yml that does not depend on
// GitHub's best-effort cron. Each Cloudflare cron tick calls workflow_dispatch;
// the workflow's guard step turns repeat runs into no-ops.
// Secret: GH_PAT, a fine-grained PAT scoped to this repo with Actions: write.

const DISPATCH_URL =
  "https://api.github.com/repos/jeffrymahbuubi/github-everyday-contributions" +
  "/actions/workflows/daily.yml/dispatches";

async function dispatch(env) {
  const res = await fetch(DISPATCH_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_PAT}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "daily-checkin-cf-trigger",
    },
    body: JSON.stringify({ ref: "main" }),
  });
  // 204 = accepted. Anything else is logged and fails the cron invocation,
  // which shows up in the Worker's Cron Events / logs.
  if (res.status !== 204) {
    throw new Error(`dispatch failed: ${res.status} ${await res.text()}`);
  }
  console.log("workflow_dispatch accepted");
}

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },
};

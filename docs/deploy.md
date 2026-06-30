# Deploying the web demo on a VPS

The web demo is a single FastAPI service with a SQLite store — no external database,
no Node. The recommended deployment is Docker Compose behind a reverse proxy that
terminates TLS.

## 1. Quick start (Docker Compose)

```bash
git clone https://github.com/scottcampbell/agent-repo-preflight.git
cd agent-repo-preflight
docker compose up -d --build
```

This builds the image, runs the app, and binds it to `127.0.0.1:8000` on the host (so it
is only reachable through your reverse proxy). Scan history persists in the
`preflight-data` Docker volume across restarts and rebuilds.

Check it:

```bash
curl -s localhost:8000/ | head -n1
docker compose logs -f web
```

## 2. TLS + public access (Caddy — automatic HTTPS)

Caddy gets you HTTPS with one config block and auto-renewing certificates. On the VPS,
point your domain's DNS A record at the server, then add a `caddy` service.

`Caddyfile`:

```
preflight.example.com {
    reverse_proxy 127.0.0.1:8000
    encode zstd gzip
}
```

Run Caddy (host network so it can reach the app on localhost):

```bash
docker run -d --name caddy --restart unless-stopped --network host \
  -v "$PWD/Caddyfile:/etc/caddy/Caddyfile" \
  -v caddy-data:/data -v caddy-config:/config \
  caddy:2
```

That's it — `https://preflight.example.com` is live with a valid certificate.

<details>
<summary>nginx alternative</summary>

```nginx
server {
    listen 443 ssl;
    server_name preflight.example.com;
    ssl_certificate     /etc/letsencrypt/live/preflight.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/preflight.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

</details>

## 3. Configuration

Set these in `docker-compose.yml` (the `environment:` block) or your shell:

| Variable | Default | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | _(none)_ | Lifts GitHub rate limits and enables private-repo scans. **Recommended** for a public instance. |
| `AGENT_PREFLIGHT_DB` | `/data/preflight.db` | SQLite path (kept on the volume). |
| `AGENT_PREFLIGHT_HOST` | `0.0.0.0` | Bind address inside the container. |
| `AGENT_PREFLIGHT_PORT` | `8000` | Bind port inside the container. |
| `AGENT_PREFLIGHT_EXAMPLES_DIR` | `/app/examples` | Where the `/examples` page is seeded from. |

Provide a token without committing it:

```bash
echo "GITHUB_TOKEN=ghp_xxx" > .env   # docker compose reads .env automatically
docker compose up -d
```

## 4. Running a *public* scan endpoint — read this

The service accepts a GitHub URL and downloads that repo's tarball to scan it. It is
safe by design — **it never executes target repository code**, only `github.com` URLs
are accepted (no local paths / SSRF), and the tarball is capped at 50 MB — but a public
endpoint still does outbound work on behalf of anonymous users. Before exposing it:

- **Set `GITHUB_TOKEN`** so GitHub doesn't rate-limit your server's IP.
- **Rate-limit at the proxy.** Each scan is synchronous and can fetch up to 50 MB, so cap
  requests per IP. Caddy example:

  ```
  preflight.example.com {
      rate_limit {
          zone scans {
              key    {remote_host}
              events 20
              window 1m
          }
      }
      reverse_proxy 127.0.0.1:8000
  }
  ```

  (Use nginx `limit_req` if you prefer nginx.)
- **Keep the app bound to localhost** (the default in `docker-compose.yml`) so the only
  way in is through the proxy.
- Scans run in-request; for heavy traffic, run multiple replicas behind the proxy. A job
  queue is on the roadmap but not required for typical use.

## 5. Updating

```bash
git pull
docker compose up -d --build
```

The volume keeps your scan history across rebuilds.

## 6. Without Docker (systemd)

```bash
python -m venv /opt/preflight/venv
/opt/preflight/venv/bin/pip install "agent-repo-preflight[web]"
```

`/etc/systemd/system/preflight.service`:

```ini
[Unit]
Description=Agent Repo Preflight web
After=network.target

[Service]
Environment=AGENT_PREFLIGHT_DB=/var/lib/preflight/preflight.db
Environment=AGENT_PREFLIGHT_HOST=127.0.0.1
ExecStart=/opt/preflight/venv/bin/python -m agent_repo_preflight.web
Restart=on-failure
User=preflight

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now preflight
```

Put the same Caddy/nginx reverse proxy in front.

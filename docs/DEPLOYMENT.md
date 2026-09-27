# Deploying ADAPPT to adappt.ietempstme.com on AWS Free Tier

This is a concrete, step-by-step runbook for a $0 deployment: one small EC2
box (Nginx + the FastAPI backend + the built frontend), one small RDS
Postgres instance, and an S3 bucket for uploads. Total footprint fits inside
a new AWS account's 12-months-free allowance if you follow the guardrails in
Phase 0.

**Region choice**: use `ap-south-1` (Mumbai) — the event is physically at
MPSTME, Mumbai, so this minimizes latency for participants and judges.

---

## Phase 0 — Safety net (do this before anything else)

You said no-budget is a hard requirement. AWS Free Tier is *usage-limited*,
not something that blocks you at the limit — if you accidentally exceed it,
AWS bills you rather than stopping you. Set alerts so you find out before
a bill does:

1. Create the AWS account, enable MFA on the **root** user, then stop using
   root for anything else.
2. Create an IAM user for yourself with `AdministratorAccess` (or use IAM
   Identity Center) — use this day-to-day, never root.
3. **Billing alarm** (do this in the first 5 minutes): AWS Console → Billing
   → Budgets → Create budget → "Zero spend budget" template. This emails
   you the moment *any* charge appears. Also add a second budget alert at
   $5 as a backstop.
4. Check **Billing → Free Tier** page weekly during the event — it shows
   exactly how much of each free allowance you've used.

---

## Phase 1 — S3 bucket (file storage)

1. S3 Console → Create bucket. Name: `adappt-uploads` (must be globally
   unique — try `adappt-mpstme-uploads` if taken). Region: `ap-south-1`.
   **Block all public access: ON** (keep it private — the app uses
   presigned URLs, nothing needs to be public).
2. Bucket → Permissions → CORS → paste this (replace the origin if you
   decide on a different domain):
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["PUT", "GET"],
       "AllowedOrigins": ["https://adappt.ietempstme.com"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3000
     }
   ]
   ```
   This is the #1 cause of "upload failed" errors on real deployments —
   without it, browsers silently block the direct-to-S3 upload with a CORS
   error that only shows up in devtools. Get this right before testing.
3. IAM → Policies → Create policy (JSON), scoped to only this bucket:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::adappt-uploads/*"
       }
     ]
   }
   ```
4. **Don't create access keys for this.** Instead, attach this policy to an
   IAM Role you'll assign to the EC2 instance in Phase 4 (an "instance
   profile"). The app's S3 client (`boto3`) automatically picks up
   instance-profile credentials with zero config — no `AWS_ACCESS_KEY_ID`/
   `AWS_SECRET_ACCESS_KEY` env vars needed, and nothing to leak if the box
   is ever compromised.

**Free tier**: 5 GB storage, 20,000 GET + 2,000 PUT requests/month, for 12
months. Video submissions can add up — check the Free Tier billing page
after Round 1 opens. Overage is cheap (~$0.023/GB/month) if it happens, it
will not break uploads, just show up as a small charge.

---

## Phase 2 — RDS Postgres

1. RDS Console → Create database → Standard create → PostgreSQL → version
   17.x → **Free tier** template.
2. Instance: `db.t3.micro` (or `db.t4g.micro` if offered). Storage: 20 GB
   gp2 (included in free tier). **Single-AZ** (Multi-AZ costs extra).
3. DB identifier: `adappt-db`. Master username: `adappt_admin`. Generate
   and save a strong master password (a password manager, not a text file).
4. **Public access: No.** VPC security group: create a new one, e.g.
   `adappt-db-sg` — you'll open port 5432 to the EC2 instance's security
   group only, in Phase 4 (never to `0.0.0.0/0`).
5. Enable automated backups (on by default, 7-day retention — free, keep
   it).
6. Once created, note the endpoint (e.g.
   `adappt-db.xxxxxxxx.ap-south-1.rds.amazonaws.com`) — you'll build
   `DATABASE_URL` from it:
   ```
   postgresql+psycopg://adappt_admin:<password>@<endpoint>:5432/adappt
   ```
   (The `adappt` database itself gets created by running migrations in
   Phase 5 — RDS just gives you the Postgres server.)

**Free tier**: 750 hrs/month db.t3.micro (covers one instance running
24/7), 20 GB storage, 20 GB backup storage, for 12 months.

---

## Phase 3 — EC2 instance

1. EC2 Console → Launch instance. AMI: **Ubuntu 24.04 LTS**. Type:
   `t3.micro` (falls back to `t2.micro` if `t3.micro` isn't free-tier
   eligible in your account — check the "Free tier eligible" tag next to
   each type in the picker).
2. Key pair: create one, download the `.pem`, keep it safe — it's your only
   SSH access.
3. Security group `adappt-web-sg`:
   - Inbound: 22 (SSH) from **your IP only** (not `0.0.0.0/0`), 80 (HTTP)
     and 443 (HTTPS) from anywhere.
   - No other inbound rules — the backend only listens on `localhost`,
     Nginx is the only public-facing process.
4. Storage: 20-30 GB gp3 (free tier covers 30 GB EBS).
5. **IAM instance role**: attach the S3 role/policy from Phase 1 here, under
   "Advanced details → IAM instance profile."
6. Launch, then allocate and associate an **Elastic IP** to it (free while
   attached to a running instance) — this way your DNS record never needs
   to change even if you stop/start the instance.
7. Update the RDS security group (Phase 2) to allow inbound 5432 from
   `adappt-web-sg` specifically.

**Free tier**: 750 hrs/month t3.micro or t2.micro, for 12 months — covers
one instance running continuously all month.

---

## Phase 4 — DNS

In whatever DNS provider manages `ietempstme.com` (Route 53 or otherwise),
add:

```
Type: A
Name: adappt
Value: <the Elastic IP from Phase 3>
TTL: 300
```

This makes `adappt.ietempstme.com` resolve to your EC2 box. DNS propagation
is usually fast (minutes) but can take up to ~an hour.

---

## Phase 5 — Deploy the app on the EC2 box

SSH in: `ssh -i your-key.pem ubuntu@<elastic-ip>`

```bash
# System packages
sudo apt update && sudo apt install -y python3-venv python3-pip nginx git

# Clone your repo (push it to GitHub/GitLab first if it isn't already)
git clone <your-repo-url> ~/adappt
cd ~/adappt/backend

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Real production .env — see the template below
nano .env
chmod 600 .env

# Migrations
alembic upgrade head

# Real content + your admin account (no demo data, no hardcoded password)
ADMIN_EMAIL=you@ietempstme.com ADMIN_PASSWORD='a-strong-password-here' \
  python -m scripts.bootstrap
```

### Production `.env` template (fill in the blanks)

```bash
ENVIRONMENT=production
DEBUG=false
API_PREFIX=/api
FRONTEND_URL=https://adappt.ietempstme.com

DATABASE_URL=postgresql+psycopg://adappt_admin:<rds-password>@<rds-endpoint>:5432/adappt

JWT_SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(64))">
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ACTIVATION_TOKEN_EXPIRE_HOURS=24

STORAGE_BACKEND=s3
AWS_REGION=ap-south-1
S3_BUCKET_NAME=adappt-uploads
PRESIGNED_URL_EXPIRE_SECONDS=3600

EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=mpstmeiete@gmail.com
SMTP_PASSWORD=<gmail App Password — see Phase 6, NOT your normal Gmail password>
EMAIL_FROM_ADDRESS=mpstmeiete@gmail.com
EMAIL_FROM_NAME=ADAPPT 5.0

REGISTRATION_SYNC_MODE=csv
PAYMENT_PER_PERSON_INR=300

CORS_ORIGINS=https://adappt.ietempstme.com
```

Note: `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are deliberately **not**
set here — the EC2 instance role from Phase 3 supplies S3 credentials
automatically.

The app **refuses to start** if `ENVIRONMENT=production` and any of
`JWT_SECRET_KEY`/`DEBUG`/`STORAGE_BACKEND`/`EMAIL_BACKEND` are still at
their dev defaults — so if it won't boot, check those four first.

### systemd service (keeps the backend running, restarts on crash)

`sudo nano /etc/systemd/system/adappt-backend.service`:

```ini
[Unit]
Description=ADAPPT backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/adappt/backend
Environment="PATH=/home/ubuntu/adappt/backend/venv/bin"
ExecStart=/home/ubuntu/adappt/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now adappt-backend
sudo systemctl status adappt-backend   # confirm it's running
```

A `t3.micro` has 1 GB RAM — 2 uvicorn workers is a safe ceiling. Add a 1 GB
swapfile as cheap insurance against OOM kills under a burst of traffic:

```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Build and serve the frontend

On your own machine (or on the box — either works):

```bash
cd frontend
npm ci
npm run build
```

Copy `dist/` to the server (if built locally): `scp -i your-key.pem -r dist ubuntu@<elastic-ip>:~/adappt-frontend-dist`

On the server:

```bash
sudo mkdir -p /var/www/adappt
sudo cp -r ~/adappt-frontend-dist/* /var/www/adappt/
```

### Nginx config

`sudo nano /etc/nginx/sites-available/adappt`:

```nginx
server {
    listen 80;
    server_name adappt.ietempstme.com;

    root /var/www/adappt;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/adappt /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Note that actual file uploads (documents, videos, payment screenshots) go
**straight from the browser to S3** via presigned URLs — they never pass
through Nginx or the backend at all. That's deliberate: it's why a 300 MB
video upload can't time out on this tiny box or hit a body-size limit here.

### HTTPS (Let's Encrypt, free, auto-renewing)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d adappt.ietempstme.com
```

Certbot edits the Nginx config to add the certificate and redirect HTTP→HTTPS,
and installs a renewal timer automatically. Confirm with:
`sudo certbot renew --dry-run`

---

## Phase 6 — Gmail SMTP setup

Gmail no longer accepts your normal account password for SMTP — you need an
**App Password**, which requires 2-Step Verification to be on:

1. Log into `mpstmeiete@gmail.com` → Google Account → Security.
2. Turn on **2-Step Verification** if it isn't already.
3. Security → "2-Step Verification" → scroll to **App passwords** → create
   one (name it "ADAPPT SMTP") → copy the 16-character password shown once.
4. Use that as `SMTP_PASSWORD` in `.env` (not the real Gmail password).

**Gmail sending limits**: 500 emails/day on a regular Gmail account. Each
activation and each submission confirmation is one email, so this comfortably
covers hundreds of teams as long as verifications trickle in rather than
all landing in the same 24 hours. If you expect a huge single-day surge
(e.g. everyone gets verified right after a payment-verification push),
watch for `550` / rate-limit errors in the backend logs — the fix then is
either spacing out admin verifications or moving to a real transactional
provider (SES/SendGrid) later, which is a one-line env var change since
email is behind an abstraction already.

---

## Phase 7 — End-to-end test before opening registration

Do this full loop yourself before announcing the link:

1. Visit `https://adappt.ietempstme.com` — confirm HTTPS padlock, no
   console errors.
2. Register a test team → upload a real payment screenshot → confirm you
   see "Payment proof received."
3. Log in as admin → verify the payment → confirm the activation email
   actually arrives (check spam folder for it too, the first send from a
   fresh address sometimes lands there).
4. Activate the test account → log in → upload both a real PPT/PDF and a
   short video on the Submission page → confirm no errors and the upload
   progress bar completes.
5. As admin, download that submission's files back — confirms the S3 CORS
   policy and presigned download URLs both work.

If step 4 fails with a CORS error in the browser console, re-check the S3
CORS policy in Phase 1 first — that's the most common cause.

---

## Ongoing during the event

- Check **Billing → Free Tier** usage weekly.
- `sudo systemctl status adappt-backend` and `sudo journalctl -u adappt-backend -f`
  if anything looks wrong.
- Consider a free uptime monitor (e.g. UptimeRobot) pinging
  `https://adappt.ietempstme.com/api/health` every 5 minutes, so you hear
  about downtime before participants do.
- RDS and EC2 both keep running (and consuming free-tier hours) even when
  idle — there's no need to stop them between Round 1 and Round 2, and
  stopping/restarting EC2 changes nothing about the Elastic IP since it
  stays associated.

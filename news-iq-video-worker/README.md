# News IQ - Video Worker Service

A standalone Python/FastAPI service that generates MP4 videos from news scripts using gTTS (free text-to-speech) + FFmpeg + PIL, uploads them to Railway S3-compatible object storage, and stores metadata in PostgreSQL.

## What It Does

1. Receives a script via HTTP POST `/generate`
2. Cleans script markers (`[PAUSE]`, `[EMPHASIS]`, `[SOUND]`)
3. Generates audio via **gTTS** (free, no API key needed)
4. Renders a title frame via **PIL** (with system fonts)
5. Encodes MP4 via **FFmpeg** (H.264 + AAC)
6. Uploads to **Railway bucket** (S3-compatible)
7. Saves metadata to **PostgreSQL**
8. Returns the bucket URL + video metadata

## Architecture

```
n8n Workflow 4          Video Worker Service          PostgreSQL / Bucket
    |                           |                            |
    | POST /generate            |                            |
    |-------------------------> |                            |
    | {script_id, title,        |                            |
    |  content, video_type }    |                            |
    |                           |---> gTTS (audio)           |
    |                           |---> PIL (frame)            |
    |                           |---> FFmpeg (MP4)           |
    |                           |---> S3 Upload              |
    |                           |---> INSERT videos table    |
    |                           |                            |
    | <-------------------------|                            |
    | {bucket_url, duration,    |                            |
    |  file_size, quality }     |                            |
```

## Prerequisites

- Railway account with an existing **News IQ project**
- PostgreSQL service already running (with `videos` table)
- Railway **bucket** already created (e.g. `news-iq-videos`)
- Bucket credentials already configured in Railway

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app with `/generate` and `/health` endpoints |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Multi-stage build with Python 3.11 + FFmpeg + fonts |
| `.dockerignore` | Keeps image small |

## Deployment to Railway

### Step 1: Create the service from this folder

You have two options:

**Option A: Deploy from GitHub (Recommended for production)**

1. Create a new GitHub repo
2. Push these 4 files to it
3. In Railway dashboard: **New Service** -> **GitHub Repo** -> Select your repo
4. Railway auto-detects the Dockerfile

**Option B: Deploy from local folder (Fastest for testing)**

```bash
# Install Railway CLI if you haven't
npm install -g @railway/cli

# Login
railway login

# Link to your News IQ project
railway link

# Create a new service from this directory
railway add --dockerfile .
```

### Step 2: Configure environment variables

In Railway dashboard -> Your new Video Worker service -> **Variables** tab, add:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@postgres.railway.internal:5432/railway
BUCKET_NAME=news-iq-videos
BUCKET_REGION=us-west-1
BUCKET_ENDPOINT=https://YOUR_BUCKET_ENDPOINT
BUCKET_ACCESS_KEY=YOUR_ACCESS_KEY
BUCKET_SECRET_KEY=YOUR_SECRET_KEY
```

> **Note:** If you already have these variables in another service, use Railway's **Reference Variables** feature instead of copying values.

### Step 3: Deploy

```bash
railway up
```

Or click **Deploy** in the Railway dashboard.

### Step 4: Verify

Once deployed, Railway will give you a public URL like:
`https://news-iq-video-worker-production.up.railway.app`

Test it:

```bash
curl https://YOUR_URL/health
```

Should return:
```json
{"status": "ok", "timestamp": "2026-08-13T..."}
```

## API Usage

### POST /generate

**Request:**
```json
{
  "script_id": "e74785b1-5744-46e1-9969-3bad0cce37b6",
  "title": "Tech Giant Announces Revolutionary AI Chip",
  "content": "[EMPHASIS]Breaking news[/EMPHASIS] from the tech world! [PAUSE] A major company just announced a revolutionary AI tool.",
  "video_type": "daily_short"
}
```

**Response:**
```json
{
  "success": true,
  "video_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "bucket_url": "https://bucket.endpoint/news-iq-videos/videos/daily_short/uuid.mp4",
  "duration_seconds": 36,
  "file_size_bytes": 1048576,
  "format": "9:16",
  "quality_score": 95.0,
  "message": "Video generated and uploaded. Quality: 95/100"
}
```

### GET /health

Returns service status. Use this for Railway health checks or monitoring.

## n8n Workflow 4 Integration

In your n8n Workflow 4 (Video Generation), replace the manual Python Console hack with an **HTTP Request** node:

**Node: Generate Video via Worker**
- **Method:** POST
- **URL:** `https://YOUR_VIDEO_WORKER_URL/generate`
- **Body (JSON):**
```json
{
  "script_id": "{{ $json.script_id }}",
  "title": "{{ $json.title }}",
  "content": "{{ $json.content }}",
  "video_type": "daily_short"
}
```
- **Timeout:** 120000ms (2 minutes - video generation takes time)

Then store the response in PostgreSQL (or the worker already does this for you).

## Video Specifications

| Type | Resolution | Aspect | Duration | Font Size |
|------|-----------|--------|----------|-----------|
| Daily Short | 1080 x 1920 | 9:16 | 30-60s | 60px |
| Weekly | 1920 x 1080 | 16:9 | 5-10min | 48px |

## Cost

- **gTTS:** Free (Google Translate TTS, no API key needed)
- **FFmpeg:** Free (open source)
- **Compute:** ~$5-10/month on Railway (shared CPU, 1GB RAM)
- **Storage:** Railway bucket pricing (first 5GB usually free tier)

## Troubleshooting

**"FFmpeg error" in response:**
- Check that FFmpeg is installed: `ffmpeg -version` inside the container
- The Dockerfile installs it, but verify the deploy succeeded

**"Database connection failed":**
- Verify `DATABASE_URL` is correct
- Check that the Video Worker service is on the same Railway private network as PostgreSQL
- Try using the internal Railway URL format: `postgresql://postgres:PASSWORD@postgres.railway.internal:5432/railway`

**"S3 upload failed":**
- Verify all 4 `BUCKET_*` variables are set
- Check that the bucket name matches exactly what Railway created
- Ensure the bucket allows public read (or use pre-signed URLs if private)

**Videos look blurry / wrong size:**
- The service auto-scales the frame to the correct resolution
- If fonts are missing, it falls back to a default font
- Check container logs for font-loading warnings

## Next Steps

1. Deploy this service
2. Test with one script via curl
3. Build n8n Workflow 4 to call it on schedule
4. Add error handling in n8n (retry on 500, alert on repeated failures)
5. Monitor bucket storage usage

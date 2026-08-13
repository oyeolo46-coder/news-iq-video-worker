#!/usr/bin/env python3
"""
Quick single-request test for the Video Worker.
Usage: python quick_test.py --url https://your-worker.railway.app
"""

import argparse
import requests
import json
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Worker base URL")
    parser.add_argument("--type", default="daily_short", choices=["daily_short", "weekly"])
    args = parser.parse_args()

    payload = {
        "script_id": f"quick-test-{datetime.now().strftime('%H%M%S')}",
        "title": "Breaking: Major Tech Announcement Today",
        "content": "[EMPHASIS]Breaking news[/EMPHASIS] from Silicon Valley! [PAUSE] A leading technology company has just unveiled its most ambitious project yet. [PAUSE] The new platform promises to reshape how we interact with artificial intelligence. [SOUND:alert] Industry analysts are already calling it a game changer. [PAUSE] Stay ahead of the curve. [EMPHASIS]Subscribe now for daily tech briefs.[/EMPHASIS]",
        "video_type": args.type,
    }

    print(f"Sending {args.type} generation request to {args.url}/generate...")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    start = datetime.now()
    resp = requests.post(f"{args.url}/generate", json=payload, timeout=180)
    elapsed = (datetime.now() - start).total_seconds()

    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed:.1f}s\n")

    try:
        data = resp.json()
        print("Response:")
        print(json.dumps(data, indent=2))

        if data.get("success"):
            print(f"\n[PASS] Video generated successfully!")
            print(f"  Video ID: {data.get('video_id')}")
            print(f"  Bucket URL: {data.get('bucket_url')}")
            print(f"  Duration: {data.get('duration_seconds')}s")
            print(f"  Size: {data.get('file_size_bytes', 0) / (1024*1024):.2f} MB")
            print(f"  Quality: {data.get('quality_score')}/100")
        else:
            print(f"\n[FAIL] Generation failed: {data.get('message')}")
    except Exception as e:
        print(f"Response body: {resp.text}")
        print(f"Parse error: {e}")

if __name__ == "__main__":
    main()

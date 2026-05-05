import feedparser
import os
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

KEYWORDS = [
    "visiting Seoul clinic",
    "trip to Korea skincare",
    "flying to Korea treatment",
    "worth flying to Seoul",
    "planning Korea trip surgery",
    "Seoul medical tourism",
    "Korea trip dermatologist",
    "Rejuran where to get Seoul",
    "Rejuran Korea trip",
    "GLP-1 Korea trip",
    "Mounjaro Korea visit",
    "Wegovy Korea cheaper",
    "Ulthera Seoul visit",
    "Exosome Seoul clinic",
    "cheaper in Korea",
    "Korea vs US price treatment",
    "medical tourism Korea worth it",
    "how much does it cost in Korea",
]

SUBREDDITS = [
    "koreatravel",
    "Seoul",
    "PlasticSurgery",
    "MedicalTourism",
    "Semaglutide",
    "Ozempic",
    "WegovyWeightLoss",
    "skincareaddiction",
    "AsianBeauty",
    "koreanskincare",
]

def check_reddit_rss():
    found = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    seen = set()
    for subreddit in SUBREDDITS:
        for keyword in KEYWORDS:
            url = f"https://www.reddit.com/r/{subreddit}/search.rss?q={keyword.replace(' ', '+')}&sort=new&restrict_sr=1"
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    if entry.link in seen:
                        continue
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    if published > cutoff:
                        seen.add(entry.link)
                        found.append({
                            'subreddit': f"r/{subreddit}",
                            'keyword': keyword,
                            'title': entry.title,
                            'link': entry.link,
                            'published': published.strftime('%Y-%m-%d %H:%M UTC'),
                            'summary': entry.summary[:300] if hasattr(entry, 'summary') else '',
                        })
            except Exception as e:
                print(f"Error: r/{subreddit} '{keyword}': {e}")
    return found

def send_slack(found_items):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print("Slack 설정 없음")
        return
    for item in found_items:
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"🔔 새 게시물 — {item['subreddit']}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*키워드:*\n{item['keyword']}"},
                        {"type": "mrkdwn", "text": f"*시간:*\n{item['published']}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*<{item['link']}|{item['title']}>*\n{item['summary'][:200]}..."}
                },
                {
                    "type": "actions",
                    "elements": [{"type": "button", "text": {"type": "plain_text", "text": "게시물 보기"}, "url": item['link'], "style": "primary"}]
                },
                {"type": "divider"}
            ]
        }
        try:
            requests.post(webhook_url, json=message)
            print(f"✅ Slack 전송: {item['title'][:50]}")
        except Exception as e:
            print(f"❌ Slack 전송 실패: {e}")

def send_email(found_items):
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_pass = os.environ.get('GMAIL_PASS')
    notify_email = os.environ.get('NOTIFY_EMAIL')
    if not all([gmail_user, gmail_pass, notify_email]):
        print("이메일 설정 없음")
        return
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔔 Telos Monitor - {len(found_items)}개 게시물 ({datetime.now().strftime('%m/%d %H:%M')})"
    msg['From'] = gmail_user
    msg['To'] = notify_email
    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;">
<div style="background:#0a1628;padding:24px;">
  <h1 style="color:#c9a96e;margin:0;">🔔 Telos Monitor</h1>
  <p style="color:#8899aa;">{datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(found_items)}개 발견</p>
</div>"""
    for item in found_items:
        html += f"""<div style="border:1px solid #e0e0e0;margin:16px 0;padding:16px;">
  <p style="color:#888;">{item['subreddit']} · {item['keyword']}</p>
  <h3><a href="{item['link']}">{item['title']}</a></h3>
  <p>{item['summary'][:200]}...</p>
</div>"""
    html += "</body></html>"
    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, notify_email, msg.as_string())
        server.quit()
        print("✅ 이메일 전송 완료")
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")

def main():
    print(f"🔍 Telos Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    found = check_reddit_rss()
    print(f"발견: {len(found)}개")
    if found:
        for item in found:
            print(f"  - [{item['subreddit']}] {item['title'][:60]}...")
        send_slack(found)
        send_email(found)
    else:
        print("✅ 새 게시물 없음")

if __name__ == "__main__":
    main()

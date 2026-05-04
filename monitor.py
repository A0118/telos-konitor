
import feedparser
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

# ── 구매 의도 있는 키워드만 ──────────────────────────────
KEYWORDS = [
    # 한국 방문 의도
    "visiting Seoul clinic",
    "trip to Korea skincare",
    "flying to Korea treatment",
    "worth flying to Seoul",
    "planning Korea trip surgery",
    "Seoul medical tourism",
    "Korea trip dermatologist",
    # 시술 + 서울/한국
    "Rejuran where to get Seoul",
    "Rejuran Korea trip",
    "GLP-1 Korea trip",
    "Mounjaro Korea visit",
    "Wegovy Korea cheaper",
    "Ulthera Seoul visit",
    "Exosome Seoul clinic",
    # 가격 비교
    "cheaper in Korea",
    "Korea vs US price treatment",
    "medical tourism Korea worth it",
    "how much does it cost in Korea",
]

# ── 서브레딧 ────────────────────────────────────────────
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

def send_email(found_items):
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_pass = os.environ.get('GMAIL_PASS')
    notify_email = os.environ.get('NOTIFY_EMAIL')
    if not all([gmail_user, gmail_pass, notify_email]):
        print("이메일 설정 없음")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔔 Telos Monitor - {len(found_items)}개 한국방문 관심 게시물 ({datetime.now().strftime('%m/%d %H:%M')})"
    msg['From'] = gmail_user
    msg['To'] = notify_email

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;">
<div style="background:#0a1628;padding:24px;border-radius:8px 8px 0 0;">
  <h1 style="color:#c9a96e;margin:0;">🔔 Telos Monitor</h1>
  <p style="color:#8899aa;margin:8px 0 0;">{datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(found_items)}개 발견 · 한국 방문 관심 게시물</p>
</div>"""

    for item in found_items:
        html += f"""
<div style="border:1px solid #e0e0e0;border-radius:8px;margin:16px 0;overflow:hidden;">
  <div style="background:#f8f8f8;padding:12px 16px;border-bottom:1px solid #e0e0e0;">
    <span style="background:#0a1628;color:#c9a96e;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:bold;">Reddit</span>
    <span style="color:#888;font-size:13px;margin-left:8px;">{item['subreddit']}</span>
    <span style="color:#aaa;font-size:12px;margin-left:8px;">· {item['published']}</span>
    <span style="color:#c9a96e;font-size:12px;margin-left:8px;">키워드: {item['keyword']}</span>
  </div>
  <div style="padding:16px;">
    <h3 style="margin:0 0 8px;"><a href="{item['link']}" style="color:#0a1628;text-decoration:none;">{item['title']}</a></h3>
    <p style="color:#667788;font-size:14px;margin:0 0 12px;line-height:1.6;">{item['summary'][:250]}...</p>
    <a href="{item['link']}" style="background:#0a1628;color:#c9a96e;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:bold;">게시물 보기 →</a>
  </div>
</div>"""

    html += """<div style="background:#f8f8f8;padding:16px;text-align:center;">
  <p style="color:#aaa;font-size:12px;margin:0;">Telos Monitor · telos.beauty · 매 1시간 자동실행</p>
</div></body></html>"""

    msg.attach(MIMEText(html, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, notify_email, msg.as_string())
        server.quit()
        print(f"✅ 이메일 전송 완료")
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")

def main():
    print(f"🔍 Telos Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    found = check_reddit_rss()
    print(f"발견: {len(found)}개")
    if found:
        for item in found:
            print(f"  - [{item['subreddit']}] {item['title'][:60]}...")
        send_email(found)
    else:
        print("✅ 새 게시물 없음")

if __name__ == "__main__":
    main()

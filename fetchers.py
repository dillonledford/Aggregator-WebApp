import requests
import feedparser
from datetime import datetime, timedelta, timezone

def fetch_feed(url, days=1):
    feed = feedparser.parse(url)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for entry in feed.entries:
        parsed = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
        if not parsed:
            continue
        published = datetime(*parsed[:6], tzinfo=timezone.utc)
        if published >= cutoff:
            items.append(f"Title: {entry.title}\nSummary: {entry.get('summary', '')}")
    return items

def fetch_github_repo(repo, days=7):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    
    # Releases via RSS
    feed = feedparser.parse(f"https://github.com/{repo}/releases.atom")
    for entry in feed.entries:
        parsed = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
        if not parsed:
            continue
        published = datetime(*parsed[:6], tzinfo=timezone.utc)
        if published >= cutoff:
            items.append(f"Release: {entry.title}\n{entry.get('summary', '')}")
    
    # Commits via GitHub API
    commits_resp = requests.get(
        f"https://api.github.com/repos/{repo}/commits",
        params={"since": cutoff.isoformat(), "per_page": 20}
    )
    if commits_resp.status_code == 200:
        for commit in commits_resp.json():
            message = commit['commit']['message'].split('\n')[0]
            date = commit['commit']['author']['date']
            items.append(f"Commit: {message} ({date})")
    
    return items

def fetch_drive_folder(folder_id, token, days=7):
    headers = {"Authorization": f"Bearer {token}"}
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.isoformat()
    
    query = f"'{folder_id}' in parents and modifiedTime > '{cutoff_str}'"
    drive_resp = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers=headers,
        params={
            "q": query,
            "fields": "files(id, name, mimeType, modifiedTime)",
            "orderBy": "modifiedTime desc"
        }
    )
    files = drive_resp.json().get('files', [])
    
    summary = f"Google Drive Folder - {len(files)} files modified in timeframe:\n\n"
    
    for file in files:
        summary += f"File: {file['name']} (modified: {file['modifiedTime']})\n"
        
        if file['mimeType'] == 'application/vnd.google-apps.document':

            doc_resp = requests.get(
                f"https://docs.googleapis.com/v1/documents/{file['id']}",
                headers=headers
            )

            doc_data = doc_resp.json()
            text = ""
            for element in doc_data.get('body', {}).get('content', []):
                for para_element in element.get('paragraph', {}).get('elements', []):
                    text += para_element.get('textRun', {}).get('content', '')
            summary += f"Content:\n{text[:2000]}\n\n"
        else:
            summary += f"Type: {file['mimeType']}\n\n"
    
    return summary
    

import os
import re
import json
import urllib.request
import urllib.error

USERNAME = "pavansharan007"
TOKEN = os.getenv("GITHUB_TOKEN")

def fetch_json(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
        
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTPError on {url}: {e.code}")
        return None
    except Exception as e:
        print(f"Error on {url}: {e}")
        return None

def get_user_stats():
    print("Fetching user data...")
    user_data = fetch_json(f"https://api.github.com/users/{USERNAME}")
    if not user_data:
        return None
        
    followers = user_data.get("followers", 0)
    
    print("Fetching repos...")
    repos = []
    page = 1
    while True:
        data = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
        
    num_repos = len(repos)
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    
    commits = 0
    additions = 0
    deletions = 0
    
    print(f"Analyzing {num_repos} repos for LOC stats (this might take a while)...")
    for i, repo in enumerate(repos):
        repo_name = repo["name"]
        contributors = fetch_json(f"https://api.github.com/repos/{USERNAME}/{repo_name}/stats/contributors")
        if isinstance(contributors, list):
            for contributor in contributors:
                if contributor.get("author", {}).get("login", "").lower() == USERNAME.lower():
                    commits += contributor.get("total", 0)
                    for week in contributor.get("weeks", []):
                        additions += week.get("a", 0)
                        deletions += week.get("d", 0)
    
    total_loc = additions - deletions
    
    return {
        "repos": num_repos,
        "contributed": num_repos, # Approximation
        "stars": stars,
        "commits": commits,
        "followers": followers,
        "loc": total_loc,
        "additions": additions,
        "deletions": deletions
    }

def update_readme(stats):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()
        
    stats_block = (
        "```diff\n"
        "  ╔══════════════════════════════════════════╗\n"
        "  ║           ⚡  GitHub Stats  ⚡            ║\n"
        "  ╠══════════════════════════════════════════╣\n"
        f"  ║  📦 Repos      : {stats['repos']:>3}                   ║\n"
        f"  ║  ⭐ Stars      : {stats['stars']:>4}                   ║\n"
        f"  ║  📝 Commits    : {stats['commits']:>6,}                 ║\n"
        f"  ║  👥 Followers  : {stats['followers']:>4}                   ║\n"
        "  ╠══════════════════════════════════════════╣\n"
        f"  ║  Lines of Code : {stats['loc']:>9,}               ║\n"
        f"+ ║  ++ Added      : {stats['additions']:>9,}               ║\n"
        f"- ║  -- Deleted    : {stats['deletions']:>9,}               ║\n"
        "  ╚══════════════════════════════════════════╝\n"
        "```\n"
        f"<!-- Last Refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} -->"
    )
    
    pattern = re.compile(r"(<!-- START_STATS -->\n)(.*?)(\n<!-- END_STATS -->)", re.DOTALL)
    new_content = pattern.sub(f"\\1{stats_block}\\3", content)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("README.md updated successfully!")

if __name__ == "__main__":
    stats = get_user_stats()
    if stats:
        update_readme(stats)
    else:
        print("Could not retrieve stats. Check rate limit or token.")
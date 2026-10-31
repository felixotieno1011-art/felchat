import re
from collections import Counter

def analyze_log_file(content: str) -> dict:
    # Split lines AND remove any empty/whitespace-only lines
    lines = [line for line in content.splitlines() if line.strip()]
    
    failed_logins = 0
    path_traversals = 0
    suspicious_ips = Counter()

    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    
    for line in lines:
        if "Failed password" in line or "401 Unauthorized" in line:
            failed_logins += 1
            match = re.search(ip_pattern, line)
            if match:
                suspicious_ips[match.group(1)] += 1
                
        if "../" in line or "%2e%2e" in line.lower():
            path_traversals += 1

    top_ips = suspicious_ips.most_common(3)

    return {
        "total_lines": len(lines),
        "failed_logins": failed_logins,
        "path_traversals": path_traversals,
        "top_attacking_ips": top_ips
    }

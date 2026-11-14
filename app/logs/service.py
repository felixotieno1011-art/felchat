import re
from collections import Counter

def analyze_log_file(content: str) -> dict:
    lines = [line for line in content.splitlines() if line.strip()]
    
    failed_logins = 0
    successful_logins_after_failures = 0
    path_traversals = 0
    suspicious_ips = Counter()
    
    # Track failures per IP to detect brute-force success
    failures_by_ip = Counter()
    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    
    for line in lines:
        ip_match = re.search(ip_pattern, line)
        ip = ip_match.group(1) if ip_match else "Unknown"

        # 1. Failed Logins (SSH, Web, Invalid User)
        if any(x in line for x in ["Failed password", "Invalid user", "401 Unauthorized", "authentication failure"]):
            failed_logins += 1
            failures_by_ip[ip] += 1
            suspicious_ips[ip] += 1
                
        # 2. Path Traversal (Handles .. / and .. \ and encoded)
        if any(x in line.lower() for x in ["../", "..\\", "%2e%2e", "%252e%252e"]):
            path_traversals += 1
            suspicious_ips[ip] += 1

        # 3. Brute-force Success Detection (Accepted password after failures)
        if "Accepted password" in line or "200 OK" in line and "login" in line.lower():
            if failures_by_ip[ip] >= 3:  # If this IP failed 3+ times before succeeding
                successful_logins_after_failures += 1
                suspicious_ips[ip] += 5 # High score for successful brute force

    top_ips = suspicious_ips.most_common(5)

    return {
        "total_lines": len(lines),
        "failed_logins": failed_logins,
        "path_traversals": path_traversals,
        "successful_logins_after_failures": successful_logins_after_failures,
        "top_attacking_ips": top_ips
    }

import re

DOMAIN_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z0-9-]{1,63})*\.[a-z]{2,}$")

def normalize_domain(raw: str) -> str:
    domain = raw.strip().lower()
    if domain.endswith("."):
        domain = domain[:-1]
    if not DOMAIN_RE.match(domain):
        raise ValueError("Invalid domain")
    return domain

def normalize_hostnames(hostnames: list[str]) -> list[str]:
    seen = set()
    result = []
    for raw in hostnames:
        host = raw.strip().lower()
        if host.endswith("."):
            host = host[:-1]
        if not host:
            continue
        if host not in seen:
            seen.add(host)
            result.append(host)
    return sorted(result)

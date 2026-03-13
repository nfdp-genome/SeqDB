"""Refresh ontology terms from remote APIs (OLS4 and Entrez)."""

import httpx


async def fetch_ols_terms(ontology_id: str, limit: int = 500) -> list[dict]:
    url = f"https://www.ebi.ac.uk/ols4/api/ontologies/{ontology_id}/terms"
    params = {"size": min(limit, 500)}
    terms = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("_embedded", {}).get("terms", []):
                if item.get("is_obsolete"):
                    continue
                terms.append({
                    "term_id": item.get("obo_id") or item.get("short_form", ""),
                    "label": item.get("label", ""),
                    "synonyms": item.get("synonyms", []),
                    "parent_id": None,
                })
        except (httpx.HTTPError, KeyError):
            pass
    return terms


async def fetch_ncbi_taxonomy(term_ids: list[str]) -> list[dict]:
    if not term_ids:
        return []
    # Placeholder for NCBI Entrez integration
    return []

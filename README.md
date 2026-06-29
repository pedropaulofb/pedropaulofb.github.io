# Pedro Paulo Favato Barcelos — professional website

This repository contains the source code, content, and machine-readable metadata for the professional and academic website of Pedro Paulo Favato Barcelos.

Website: <https://pedropaulofb.github.io/>

The site presents selected work on ontology engineering, semantic interoperability, Semantic Web technologies, conceptual modeling, FAIR metadata, publications, projects, and machine-readable professional profile metadata.

## Overview

The website is built with MkDocs Material and published with GitHub Pages.

It is designed to be readable by both humans and machines. In addition to the visible website pages, the repository includes structured metadata, crawler discovery files, reuse guidance, and citation metadata.

## Main pages

- Home: <https://pedropaulofb.github.io/>
- About: <https://pedropaulofb.github.io/about/>
- Expertise: <https://pedropaulofb.github.io/expertise/>
- Projects: <https://pedropaulofb.github.io/projects/>
- Publications: <https://pedropaulofb.github.io/publications/>
- Contact: <https://pedropaulofb.github.io/contact/>
- Reuse and attribution: <https://pedropaulofb.github.io/reuse/>

## Machine-readable metadata

The site exposes two machine-readable profile serializations:

- schema.org JSON-LD profile: <https://pedropaulofb.github.io/profile.jsonld>
- RDF/Turtle profile: <https://pedropaulofb.github.io/profile.ttl>

The main internal URI for the person entity is: <https://pedropaulofb.github.io/profile.jsonld#person>

The profile metadata links to external identity and scholarly profile records, including ORCID, DBLP, Google Scholar, LinkedIn, GitHub, and w3id.org aliases.

The homepage also includes a compact inline JSON-LD summary for the website and profile page. [`profile.jsonld`](./docs/profile.jsonld) remains the canonical complete machine-readable source, while [`profile.ttl`](./docs/profile.ttl) is generated from it as an RDF/Turtle serialization for Linked Data tooling.

The generated Turtle file is checked in CI with [`scripts/generate_profile_ttl.py`](./scripts/generate_profile_ttl.py) to reduce drift between the two serializations.

## Crawler discovery

The site includes:

- robots.txt: <https://pedropaulofb.github.io/robots.txt>
- sitemap.xml: <https://pedropaulofb.github.io/sitemap.xml>

The crawler policy allows normal crawling and declares the sitemap location.

## Repository structure

- `docs/` — website source pages and static files served by MkDocs
- `docs/profile.jsonld` — canonical machine-readable JSON-LD profile
- `docs/profile.ttl` — generated RDF/Turtle profile derived from `docs/profile.jsonld`
- `docs/robots.txt` — crawler policy
- `docs/reuse.md` — reuse and attribution guidance
- `overrides/main.html` — MkDocs Material template override for metadata links, page descriptions, and inline homepage JSON-LD
- `scripts/generate_profile_ttl.py` — generator and CI check for the Turtle profile
- `scripts/validate_site_references.py` — lightweight validation and reporting for site references, publication entries, and metadata consistency
- `mkdocs.yml` — MkDocs configuration
- `.github/workflows/` — GitHub Actions deployment and validation workflows
- `.pre-commit-config.yaml` — optional local quality checks for Markdown, YAML, JSON, generated metadata, and site-maintenance validation
- `CITATION.cff` — citation metadata for the website and machine-readable profile metadata
- `LICENSE` — repository license

## Publication records

The Publications page lists selected publications and accepted papers most relevant to ontology engineering, conceptual modeling, Semantic Web implementation, semantic interoperability, knowledge representation, and reusable semantic artifacts.

For broader and more frequently updated publication records, see the linked Google Scholar, ORCID, and DBLP profiles.

This repository intentionally does not currently maintain local BibTeX or CSL-JSON publication files, to avoid duplicating and manually curating publication metadata already maintained in external scholarly profile systems.

The current maintenance model is manual curation plus lightweight validation:

- `docs/publications.md` remains the source of truth for selected publications.
- External scholarly profiles and DOI/publisher/conference pages are authority checks, not generation sources.
- `scripts/validate_site_references.py` checks repeated publication-entry structure, DOI-link format, duplicate headings, placeholders, status-sensitive links, and optional external HTTP status.
- Local BibTeX, CSL-JSON, ORCID import, and YAML/JSON-backed generation are deferred unless the selected-publication page grows enough to justify duplicated structured data.

## Site maintenance validation

Run the local validation script before committing changes that affect pages, links, metadata, or publications:

```bash
python scripts/validate_site_references.py --repo-root .
```

To run external HTTP checks and write a Markdown report:

```bash
python scripts/validate_site_references.py --repo-root . --check-external --report site-maintenance-validation.md
```

The validation script reports:

- missing required site files;
- MkDocs navigation and social-link consistency;
- profile JSON-LD and generated Turtle profile consistency;
- exposure of JSON-LD and Turtle profile links from the MkDocs template;
- internal-link target existence;
- publication-entry structure and DOI/status-sensitive link checks;
- an external URL inventory;
- optional external HTTP status warnings.

The GitHub Actions workflow `.github/workflows/validate-site-references.yml` runs the generated Turtle profile check and the site-maintenance validator on relevant pushes and pull requests, weekly, and by manual dispatch.

## Local pre-commit checks

Install pre-commit hooks with:

```bash
pre-commit install
```

Run all regular hooks manually with:

```bash
pre-commit run --all-files
```

Run the heavier MkDocs build hook manually with:

```bash
pre-commit run mkdocs-build-strict --hook-stage manual --all-files
```

The pre-commit configuration includes general repository quality hooks for whitespace, line endings, YAML/JSON/TOML syntax, merge-conflict markers, large files, private keys, Python syntax, and debug statements. It also includes local hooks for `profile.jsonld`, generated `profile.ttl`, and site-maintenance validation.

## Reuse and attribution

Reuse expectations for website content, source code, machine-readable metadata, publication metadata, and external identifiers are described at <https://pedropaulofb.github.io/reuse/>.

## Citation

Citation metadata is provided in [`CITATION.cff`](./CITATION.cff).

If citing this website or reusing its machine-readable profile metadata, please cite the website using the citation information provided by GitHub or the metadata in [`CITATION.cff`](./CITATION.cff).

## License

The repository source code is licensed under the MIT License unless otherwise stated.

Website content, publication metadata, machine-readable metadata, and third-party identifiers are subject to the reuse and attribution guidance described on the website.

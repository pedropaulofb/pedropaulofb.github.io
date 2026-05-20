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

The site exposes a schema.org JSON-LD profile: <https://pedropaulofb.github.io/profile.jsonld>

The main internal URI for the person entity is: <https://pedropaulofb.github.io/profile.jsonld#person>

The profile metadata links to external identity and scholarly profile records, including ORCID, DBLP, Google Scholar, LinkedIn, GitHub, and w3id.org aliases.

The homepage also includes a compact inline JSON-LD summary for the website and profile page, while [`profile.jsonld`](./docs/profile.jsonld) remains the canonical complete machine-readable profile.

## Crawler discovery

The site includes:

- robots.txt: <https://pedropaulofb.github.io/robots.txt>
- sitemap.xml: <https://pedropaulofb.github.io/sitemap.xml>

The crawler policy allows normal crawling and declares the sitemap location.

## Repository structure

- `docs/` — website source pages and static files served by MkDocs
- `docs/profile.jsonld` — canonical machine-readable JSON-LD profile
- `docs/robots.txt` — crawler policy
- `docs/reuse.md` — reuse and attribution guidance
- `overrides/main.html` — MkDocs Material template override for metadata links, page descriptions, and inline homepage JSON-LD
- `mkdocs.yml` — MkDocs configuration
- `.github/workflows/` — GitHub Actions deployment workflow
- `CITATION.cff` — citation metadata for the website and machine-readable profile metadata
- `LICENSE` — repository license

## Publication records

The Publications page lists selected publications and accepted papers most relevant to ontology engineering, conceptual modeling, Semantic Web implementation, semantic interoperability, knowledge representation, and reusable semantic artifacts.

For broader and more frequently updated publication records, see the linked Google Scholar, ORCID, and DBLP profiles.

This repository intentionally does not currently maintain local BibTeX or CSL-JSON publication files, to avoid duplicating and manually curating publication metadata already maintained in external scholarly profile systems.

## Reuse and attribution

Reuse expectations for website content, source code, machine-readable metadata, publication metadata, and external identifiers are described at <https://pedropaulofb.github.io/reuse/>.

## Citation

Citation metadata is provided in [`CITATION.cff`](./CITATION.cff).

If citing this website or reusing its machine-readable profile metadata, please cite the website using the citation information provided by GitHub or the metadata in [`CITATION.cff`](./CITATION.cff).

## License

The repository source code is licensed under the MIT License unless otherwise stated.

Website content, publication metadata, machine-readable metadata, and third-party identifiers are subject to the reuse and attribution guidance described on the website.

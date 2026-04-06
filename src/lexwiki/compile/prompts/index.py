"""Prompt templates for index page generation."""

INDEX_SYSTEM = """\
You maintain index pages for a legal knowledge base wiki stored as Obsidian-compatible markdown. \
Each index is a navigable table of contents using [[wikilinks]]."""

MASTER_INDEX_PROMPT = """\
Generate the master index page (_index.md) for this legal knowledge base.

All wiki pages with their frontmatter:
{pages_manifest}

Create a comprehensive index with:
1. A brief overview of the knowledge base scope
2. Quick stats (total docs, by type, by jurisdiction)
3. Organized sections by document type, each with [[page-name]] links and one-line descriptions
4. A "Recent additions" section for the 5 most recently compiled pages

Use [[page-name]] links (filename without extension). Start with a # heading.
"""

TYPE_INDEX_PROMPT = """\
Generate the document type index page (_by_type.md).

All wiki pages with their frontmatter:
{pages_manifest}

Group all documents by type (contracts, statutes, case law, memos, regulations, other). \
Within each group, list documents with [[page-name]] links and brief descriptions. \
Include document count per type.
"""

JURISDICTION_INDEX_PROMPT = """\
Generate the jurisdiction index page (_by_jurisdiction.md).

All wiki pages with their frontmatter:
{pages_manifest}

Group all documents by jurisdiction. Within each group, list documents with [[page-name]] links \
and brief descriptions. Include document count per jurisdiction.
"""

PARTY_INDEX_PROMPT = """\
Generate the party/entity index page (_by_party.md).

All wiki pages with their content summaries:
{pages_manifest}

Instructions:
1. Read through ALL the wiki pages above carefully
2. Extract every named party, entity, company, person, and organization mentioned
3. For each entity, list every document they appear in using [[page-name]] links
4. Describe their role in each document (e.g. "investor", "company", "founder", "disclosing party")
5. Group related entities together (e.g. same company appearing in multiple documents)

The output should be a comprehensive markdown page with ## headings for each major entity \
and bullet points listing their document appearances with [[page-name]] links.
"""

CLAUSE_LIBRARY_PROMPT = """\
Generate the clause library page (_clause_library.md).

All contract pages in the wiki:
{pages_manifest}

Extract and categorize standard clauses found across contracts:
- Limitation of Liability
- Indemnification
- Termination
- Confidentiality / NDA
- IP Ownership
- Force Majeure
- Governing Law / Dispute Resolution
- Data Protection
- Non-Compete / Non-Solicitation
- Payment Terms
- Any other notable clause types

For each clause type, list which contracts contain it with [[page-name]] links, \
and note any significant variations between contracts.
"""

PRECEDENT_MAP_PROMPT = """\
Generate the precedent map page (_precedent_map.md).

All case law and statute pages in the wiki:
{pages_manifest}

Map the citation relationships:
- Which cases cite which statutes
- Which cases cite other cases
- Which statutes reference other statutes
- Key precedents and their influence

Use [[page-name]] links. Present as a structured relationship map.
"""

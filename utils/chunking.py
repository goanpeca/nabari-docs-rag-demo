"""Utilities for chunking markdown documents semantically."""

import re
from typing import Any

import yaml


def extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content.

    Parameters
    ----------
    content : str
        Raw markdown content

    Returns
    -------
    tuple[dict[str, Any], str]
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    frontmatter: dict[str, Any] = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                content = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, content


def convert_relative_links_to_absolute(content: str) -> str:
    """Convert relative markdown links to absolute nebari.dev URLs.

    Examples
    --------
    >>> convert_relative_links_to_absolute("[text](guide)")
    '[text](https://nebari.dev/docs/guide)'
    >>> convert_relative_links_to_absolute("![alt](/img/pic.png)")
    '![alt](https://nebari.dev/img/pic.png)'

    Parameters
    ----------
    content : str
        Markdown content with relative links

    Returns
    -------
    str
        Content with absolute nebari.dev URLs
    """

    def replace_link(match: re.Match[str]) -> str:
        # Check if it's an image link (starts with !)
        is_image = match.group(0).startswith("!")
        link_text = match.group(1)
        link_url = match.group(2)

        # Skip if already absolute URL
        if link_url.startswith("http://") or link_url.startswith("https://"):
            return match.group(0)

        # Skip anchors
        if link_url.startswith("#"):
            return match.group(0)

        # Handle images differently - they're at /img/ not /docs/img/
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".svg")
        if is_image or "/img/" in link_url or link_url.endswith(image_extensions):
            # Remove leading slashes and ../
            clean_url = link_url.replace("../", "").replace("./", "")
            if clean_url.startswith("/"):
                clean_url = clean_url[1:]
            # Images go to root /img/ path
            if not clean_url.startswith("img/"):
                clean_url = clean_url.replace("static/img/", "img/")
            absolute_url = f"https://nebari.dev/{clean_url}"
        else:
            # Documentation links go to /docs/ path
            clean_url = link_url.replace("../", "").replace("./", "").replace("/docs/", "")
            if clean_url.startswith("/"):
                clean_url = clean_url[1:]
            absolute_url = f"https://nebari.dev/docs/{clean_url}"

        prefix = "!" if is_image else ""
        return f"{prefix}[{link_text}]({absolute_url})"

    # Match markdown links: [text](url) and images: ![alt](url)
    pattern = r"!?\[([^\]]+)\]\(([^\)]+)\)"
    return re.sub(pattern, replace_link, content)


def chunk_by_headers(
    markdown_content: str,
    metadata: dict[str, Any],
    max_chunk_size: int = 800,
    overlap: int = 100,
) -> list[tuple[str, dict[str, Any]]]:
    """Split markdown by H2/H3 headings preserving hierarchy.

    Each chunk includes:
    - Document title (from metadata)
    - Section heading
    - Section content (with relative links converted to absolute)
    - Parent context for better retrieval

    Parameters
    ----------
    markdown_content : str
        Markdown text to chunk
    metadata : dict[str, Any]
        Document metadata (title, category, file_path)
    max_chunk_size : int, default 800
        Maximum tokens per chunk
    overlap : int, default 100
        Token overlap between chunks

    Returns
    -------
    list[tuple[str, dict[str, Any]]]
        List of (chunk_text, chunk_metadata) tuples
    """
    # Convert relative links to absolute nebari.dev URLs
    markdown_content = convert_relative_links_to_absolute(markdown_content)

    chunks: list[tuple[str, dict[str, Any]]] = []

    # Split by headers (H2 and H3)
    # Pattern matches: ## Header or ### Header
    header_pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)

    # Find all headers and their positions
    headers: list[dict[str, Any]] = []
    for match in header_pattern.finditer(markdown_content):
        level = len(match.group(1))  # Number of # characters
        title = match.group(2).strip()
        start_pos = match.start()
        headers.append({"level": level, "title": title, "start": start_pos})

    # If no headers found, treat entire content as one chunk
    if not headers:
        chunk_text = f"**{metadata.get('title', 'Document')}**\n\n{markdown_content}"
        chunk_metadata = {
            **metadata,
            "heading": metadata.get("title", "Document"),
            "chunk_index": 0,
        }
        chunks.append((chunk_text, chunk_metadata))
        return chunks

    # Create chunks from sections
    for i, header in enumerate(headers):
        # Get content between this header and the next
        start = header["start"]
        end = headers[i + 1]["start"] if i + 1 < len(headers) else len(markdown_content)

        section_content = markdown_content[start:end].strip()

        # Build chunk with context
        chunk_text = f"**{metadata.get('title', 'Document')}**\n\n{section_content}"

        # Create metadata for this chunk
        chunk_metadata = {
            **metadata,
            "heading": header["title"],
            "chunk_index": i,
            "heading_level": header["level"],
        }

        # Basic token counting (rough estimate: 1 token ≈ 4 chars)
        estimated_tokens = len(chunk_text) // 4

        # If chunk is too large, split further by paragraphs
        if estimated_tokens > max_chunk_size:
            paragraphs = section_content.split("\n\n")
            current_chunk = f"**{metadata.get('title', 'Document')}**\n\n{header['title']}\n\n"

            for para in paragraphs:
                if len(current_chunk) // 4 + len(para) // 4 > max_chunk_size:
                    # Save current chunk
                    chunks.append((current_chunk.strip(), chunk_metadata.copy()))
                    # Start new chunk with overlap
                    title = metadata.get("title", "Document")
                    header_title = header["title"]
                    current_chunk = f"**{title}**\n\n{header_title}\n\n{para}\n\n"
                else:
                    current_chunk += para + "\n\n"

            # Add remaining content
            if current_chunk.strip():
                chunks.append((current_chunk.strip(), chunk_metadata.copy()))
        else:
            chunks.append((chunk_text, chunk_metadata))

    return chunks


def strip_mdx_components(content: str) -> str:
    """Remove MDX-specific React components keeping plain text.

    Parameters
    ----------
    content : str
        MDX content

    Returns
    -------
    str
        Plain markdown text
    """
    # Remove import statements
    content = re.sub(r"^import\s+.+$", "", content, flags=re.MULTILINE)

    # Remove JSX-style components (e.g., <Component prop="value">content</Component>)
    # Keep the content inside
    # Run multiple times to handle nested components like <Tabs><TabItem>...</TabItem></Tabs>
    max_iterations = 10
    for _ in range(max_iterations):
        prev_content = content
        content = re.sub(r"<(\w+)[^>]*>(.*?)</\1>", r"\2", content, flags=re.DOTALL)
        # Stop if no more changes
        if content == prev_content:
            break

    # Remove self-closing components (e.g., <Component />)
    content = re.sub(r"<\w+[^>]*/>", "", content)

    # Remove curly braces expressions (e.g., {variable})
    content = re.sub(r"\{[^}]+\}", "", content)

    return content.strip()

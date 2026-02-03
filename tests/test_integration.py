"""Integration tests for the full pipeline."""

from utils.chunking import chunk_by_headers, extract_frontmatter, strip_mdx_components


class TestEndToEndProcessing:
    """Test the full document processing pipeline."""

    def test_architecture_document_processing(self):
        """Test processing architecture.mdx from end to end."""
        # Simulate architecture.mdx content
        content = """---
id: infrastructure-architecture
title: Nebari architecture
---

# Nebari architecture

Below are the architecture diagrams.

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
  <TabItem value="gcp" label="Google GCP" default>

![GCP Architecture Diagram](/img/explanations/architecture-diagram-gcp.png)

</TabItem>

<TabItem value="aws" label="Amazon AWS">

![AWS Architecture Diagram](/img/explanations/architecture-diagram-aws.png)

</TabItem>
</Tabs>
"""

        # Step 1: Extract frontmatter
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter["title"] == "Nebari architecture"

        # Step 2: Strip MDX components
        cleaned = strip_mdx_components(body)

        # Verify images are preserved
        assert "![GCP Architecture Diagram]" in cleaned
        assert "![AWS Architecture Diagram]" in cleaned

        # Verify JSX is removed
        assert "<Tabs>" not in cleaned
        assert "<TabItem>" not in cleaned
        assert "import" not in cleaned

        # Step 3: Chunk the content
        metadata = {
            "file_path": "explanations/architecture.mdx",
            "category": "explanations",
            "title": frontmatter["title"],
        }

        chunks = chunk_by_headers(cleaned, metadata)

        # Should have multiple chunks
        assert len(chunks) > 0

        # At least one chunk should contain the images
        image_chunks = [chunk for chunk, _ in chunks if "![" in chunk]
        assert len(image_chunks) > 0

        # Verify image URLs are absolute
        for chunk, _ in chunks:
            if "![" in chunk:
                assert "https://nebari.dev/img/" in chunk


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_multiple_images_in_chunk(self):
        """Test that chunks can contain multiple images."""
        content = """# Section

![Image 1](/img/test1.png)

Some text.

![Image 2](/img/test2.png)
"""
        metadata = {"file_path": "test.md", "category": "test", "title": "Test"}
        chunks = chunk_by_headers(content, metadata)

        # Find chunk with images
        image_chunk = None
        for chunk_text, _ in chunks:
            if "![Image 1]" in chunk_text and "![Image 2]" in chunk_text:
                image_chunk = chunk_text
                break

        assert image_chunk is not None
        assert image_chunk.count("![") == 2

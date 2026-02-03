"""Tests for chunking utilities."""

from utils.chunking import (
    convert_relative_links_to_absolute,
    extract_frontmatter,
    strip_mdx_components,
)


class TestFrontmatterExtraction:
    """Test YAML frontmatter extraction."""

    def test_extract_frontmatter_basic(self):
        """Test basic frontmatter extraction."""
        content = """---
title: Test Document
description: A test
---

# Content here"""

        frontmatter, body = extract_frontmatter(content)
        assert frontmatter["title"] == "Test Document"
        assert frontmatter["description"] == "A test"
        assert body.startswith("# Content here")

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "# Just a heading"
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter == {}
        assert body == content


class TestLinkConversion:
    """Test relative to absolute link conversion."""

    def test_convert_doc_links(self):
        """Test documentation link conversion."""
        content = "[Guide](guide/install.md)"
        result = convert_relative_links_to_absolute(content)
        assert "https://nebari.dev/docs/guide/install.md" in result

    def test_convert_image_links(self):
        """Test image link conversion."""
        content = "![Diagram](/img/architecture.png)"
        result = convert_relative_links_to_absolute(content)
        assert "https://nebari.dev/img/architecture.png" in result

    def test_preserve_absolute_links(self):
        """Test that absolute links are not modified."""
        content = "[External](https://example.com)"
        result = convert_relative_links_to_absolute(content)
        assert result == content

    def test_image_not_in_docs_path(self):
        """Test that images don't get /docs/ prefix."""
        content = "![Test](../img/test.png)"
        result = convert_relative_links_to_absolute(content)
        assert "https://nebari.dev/img/test.png" in result
        assert "/docs/img/" not in result


class TestMDXStripping:
    """Test MDX component stripping."""

    def test_strip_simple_component(self):
        """Test stripping simple JSX component."""
        content = "<Tabs>Content here</Tabs>"
        result = strip_mdx_components(content)
        assert result == "Content here"
        assert "<Tabs>" not in result

    def test_strip_nested_components(self):
        """Test stripping nested JSX components."""
        content = """<Tabs>
  <TabItem value="test">
    ![Image](test.png)
  </TabItem>
</Tabs>"""
        result = strip_mdx_components(content)
        assert "![Image](test.png)" in result
        assert "<Tabs>" not in result
        assert "<TabItem>" not in result

    def test_preserve_images(self):
        """Test that markdown images are preserved."""
        content = "<Tabs>![Diagram](/img/test.png)</Tabs>"
        result = strip_mdx_components(content)
        assert "![Diagram](/img/test.png)" in result

    def test_remove_imports(self):
        """Test that import statements are removed."""
        content = "import Tabs from '@theme/Tabs';\n\nContent"
        result = strip_mdx_components(content)
        assert "import" not in result
        assert "Content" in result

    def test_architecture_mdx_example(self):
        """Test real architecture.mdx structure."""
        content = """<Tabs>
  <TabItem value="gcp" label="Google GCP" default>
![GCP Architecture Diagram](/img/explanations/architecture-diagram-gcp.png)
</TabItem>
<TabItem value="aws" label="Amazon AWS">
![AWS Architecture Diagram](/img/explanations/architecture-diagram-aws.png)
</TabItem>
</Tabs>"""
        result = strip_mdx_components(content)

        # All images should be present
        assert result.count("![") == 2
        assert "architecture-diagram-gcp.png" in result
        assert "architecture-diagram-aws.png" in result

        # No JSX tags should remain
        assert "<Tabs>" not in result
        assert "<TabItem>" not in result
        assert "label=" not in result

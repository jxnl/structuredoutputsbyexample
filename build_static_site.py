#!/usr/bin/env python3
"""
Static Site Generator for Structured Outputs by Example.

This script generates a complete static site from the examples.json file,
following the same layout and styling as the original examples site.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from html import escape
from typing import List, Dict, Any, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Site constants
SITE_TITLE = "Structured Outputs by Example"
SITE_DESCRIPTION = "Learn to work with structured outputs through annotated examples"


def load_examples_data() -> Dict[str, Any]:
    """Load examples and sections from the JSON file."""
    try:
        data_file = Path(__file__).parent / "data" / "examples.json"
        logger.info("Loading examples from %s" % data_file)
        with open(data_file, "r") as f:
            data = json.load(f)

        examples = data.get("examples", [])
        sections = data.get("sections", [])
        logger.info(
            "Loaded %d examples and %d sections" % (len(examples), len(sections))
        )
        return {"examples": examples, "sections": sections}
    except Exception as e:
        logger.error("Error loading examples: %s" % e)
        return {"examples": [], "sections": []}


def load_examples() -> List[Dict[str, Any]]:
    """Load examples from the JSON file (backward compatibility)."""
    return load_examples_data().get("examples", [])


def find_next_example(
    examples: List[Dict[str, Any]], current_example: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Find the next example based on the example order and section.
    This function respects section organization, continuing to the next section when needed.

    Args:
        examples: List of all examples
        current_example: The current example

    Returns:
        The next example or None if there is no next example
    """
    current_order = current_example["order"]
    current_section_id = current_example.get("section_id")

    # First, try to find the next example in the same section
    if current_section_id:
        same_section_examples = [
            e for e in examples if e.get("section_id") == current_section_id
        ]
        for example in sorted(same_section_examples, key=lambda e: e["order"]):
            if example["order"] > current_order:
                return example

    # If we're at the end of a section or there's no section info,
    # find the next example in any section
    for example in sorted(examples, key=lambda e: e["order"]):
        if example["order"] > current_order:
            return example

    return None


def find_prev_example(
    examples: List[Dict[str, Any]], current_example: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Find the previous example based on the example order and section.
    This function respects section organization, going back to the previous section when needed.

    Args:
        examples: List of all examples
        current_example: The current example

    Returns:
        The previous example or None if there is no previous example
    """
    current_order = current_example["order"]
    current_section_id = current_example.get("section_id")

    # First, try to find the previous example in the same section
    if current_section_id:
        same_section_examples = [
            e for e in examples if e.get("section_id") == current_section_id
        ]
        prev_example = None
        for example in sorted(
            same_section_examples, key=lambda e: e["order"], reverse=True
        ):
            if example["order"] < current_order:
                return example

    # If we're at the beginning of a section or there's no section info,
    # find the previous example in any section
    prev_example = None
    for example in sorted(examples, key=lambda e: e["order"], reverse=True):
        if example["order"] < current_order:
            return example

    return None


def generate_html_head(
    title: str, include_main_css: bool = True, base_url: str = ".", 
    description: str = None, page_type: str = "article", 
    canonical_path: str = "", example_data: Dict[str, Any] = None
) -> str:
    """Generate HTML head section with enhanced SEO elements.

    Args:
        title: The page title
        include_main_css: Whether to include CSS styles
        base_url: The base URL for relative links (default: "." for current directory)
        description: Page-specific description (falls back to site description)
        page_type: Schema.org type for the page ("article", "website", etc.)
        canonical_path: Path for canonical URL (if empty, no canonical URL is added)
        example_data: Example data for structured data generation
    """
    # Use provided description or fall back to site description
    page_description = description if description else SITE_DESCRIPTION
    
    # Base site URL
    site_url = "https://structuredoutputsbyexample.com"
    
    # Canonical URL
    canonical_url = f"{site_url}/{canonical_path}" if canonical_path else site_url
    
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Primary Meta Tags -->
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(page_description)}">
    <meta name="author" content="Jason Liu">
    <meta name="keywords" content="structured outputs, LLM, Instructor, Pydantic, data extraction, structured data">
    
    <!-- Canonical URL -->
    {f'<link rel="canonical" href="{canonical_url}">' if canonical_path else ''}
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="{page_type}">
    <meta property="og:url" content="{canonical_url if canonical_path else site_url}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(page_description)}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="{canonical_url if canonical_path else site_url}">
    <meta property="twitter:title" content="{escape(title)}">
    <meta property="twitter:description" content="{escape(page_description)}">
"""

    # Add structured data JSON-LD if we have example data
    if example_data and page_type == "article":
        # Import json here to avoid circular imports
        import json
        from datetime import datetime
        
        # Extract section title if available
        section_title = example_data.get("section_title", "")
        
        # Extract code keywords (use the example ID as a fallback)
        keywords = ["structured data", "LLM", "Instructor", "Pydantic"]
        if example_data.get("id"):
            # Convert "001-example-name" to "example name" for keywords
            example_keyword = "-".join(example_data["id"].split("-")[1:])
            keywords.append(example_keyword.replace("-", " "))
        
        # Generate JSON-LD for TechArticle
        json_ld = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": example_data.get("title", title),
            "description": page_description,
            "author": {
                "@type": "Person",
                "name": "Jason Liu"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Structured Outputs by Example",
                "url": site_url
            },
            "mainEntityOfPage": canonical_url if canonical_path else site_url,
            "datePublished": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "dateModified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "articleSection": section_title,
            "keywords": keywords
        }
        
        head += f"""
    <!-- Structured Data / JSON-LD -->
    <script type="application/ld+json">
    {json.dumps(json_ld, indent=2)}
    </script>
"""
    
    head += """
    <!-- Stylesheets -->
    <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css'>
    <script src='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js'></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/firacode@6.2.0/distr/fira_code.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');
        
        code, pre code, .hljs {
            font-family: 'Fira Code', 'JetBrains Mono', monospace;
            font-feature-settings: "liga" 1;
        }
        
        @supports (font-variation-settings: normal) {
            code, pre code, .hljs {
                font-family: 'Fira Code VF', 'JetBrains Mono', monospace;
            }
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', (event) => {
            hljs.highlightAll();
        });
    </script>
"""
    if include_main_css:
        head += """    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: #222;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px;
        }
        header {
            border-bottom: 1px solid #eee;
            padding: 15px 0;
            margin-bottom: 20px;
        }
        .site-title {
            text-decoration: none;
            color: #0066CC;
            font-weight: 500;
            font-size: 20px;
        }
        main {
            padding-bottom: 40px;
        }
        footer {
            border-top: 1px solid #eee;
            padding: 15px 0;
            margin-top: 20px;
            color: #666;
            font-size: 0.9em;
        }
        h1 {
            font-size: 36px;
            font-weight: 500;
            margin: 0 0 25px 0;
            color: #333;
        }
        p {
            margin: 20px 0;
            color: #444;
            line-height: 1.6;
        }
        a {
            color: #0066CC;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .example-link {
            margin: 4px 0;
            line-height: 1.3;
        }
        .row {
            display: flex;
            width: 100%;
            margin-bottom: 30px;
            gap: 40px;
        }
        .docs {
            flex: 0.75;
            min-width: 0;
            color: #444;
            line-height: 1.6;
            font-size: 1em;
        }
        .code {
            flex: 2.25;
            min-width: 0;
            position: relative;
        }
        pre {
            margin: 0;
            padding: 20px;
            background-color: #f8f8f8;
            border-radius: 5px;
            overflow-x: auto;
            line-height: 1.5;
        }
        /* Prevent double styling from highlight.js */
        pre code.hljs, pre code {
            background-color: transparent;
            padding: 0;
            margin: 0;
            border: none;
        }
        .leading {
            margin-bottom: 5px;
        }
        hr {
            border: none;
            border-top: 1px solid #eee;
            margin: 20px 0;
        }
        .buttons {
            position: absolute;
            top: 5px;
            right: 5px;
            z-index: 10;
        }
        .copy {
            cursor: pointer;
            width: 18px;
            height: 18px;
            opacity: 0.6;
            color: #666;
            background-color: #f8f8f8;
            border-radius: 3px;
            padding: 3px;
        }
        .copy:hover {
            opacity: 1;
            color: #0066CC;
        }
        .tooltip {
            position: absolute;
            background: #333;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            top: -25px;
            right: 0;
        }
        .command-prompt {
            color: #888;
        }
        .command-text {
            font-weight: bold;
        }
        .navigation {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }
        .prev, .next {
            margin: 5px 0;
            font-weight: 500;
        }
        .prev {
            margin-right: auto;
        }
        .next {
            margin-left: auto;
        }
        .prev span, .next span {
            color: #666;
            font-weight: normal;
        }
        @media (max-width: 900px) {
            .row {
                flex-direction: column;
            }
            .docs, .code {
                width: 100%;
            }
            .newsletter-banner {
                flex-direction: column;
                gap: 10px;
                align-items: stretch !important;
            }
            .newsletter-banner > span {
                text-align: center;
                margin-bottom: 5px;
            }
            .newsletter-banner > div {
                width: 100% !important;
            }
        }
    </style>
"""
    
    # Add PostHog tracking script
    head += """    <!-- PostHog Analytics -->
    <script>
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSurveysLoaded onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey canRenderSurveyAsync identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    posthog.init('phc_3BLxAMqz3UaIZ3My7F034KHaU2jRQpVIG9HOAdR3HXc', {
        api_host: 'https://us.i.posthog.com',
        person_profiles: 'identified_only', // or 'always' to create profiles for anonymous users as well
    })
    </script>
"""
    
    head += f"""</head>
<body>
    <div class="container">
        <header style="display: flex; justify-content: space-between; align-items: center;">
            <a href="{base_url}/" class="site-title">Structured Outputs by Example</a>
            <a href="https://github.com/jxnl/structuredoutputsbyexample" target="_blank" style="display: inline-flex; align-items: center; font-size: 0.9em; color: #0066CC; text-decoration: none; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
                Star on GitHub
            </a>
        </header>
        
        <div class="newsletter-banner" style="background-color: #f1f8ff; border-radius: 5px; padding: 10px 15px; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; font-size: 0.9em;">
            <span>Stay updated when new content is added and get tips from the Instructor team</span>
            <div style="width: 40%;">
                <iframe src="https://embeds.beehiiv.com/2faf420d-8480-4b6e-8d6f-9c5a105f917a?slim=true" data-test-id="beehiiv-embed" height="52" width="100%" frameborder="0" scrolling="no" style="margin: 0; border-radius: 0px !important; background-color: transparent;"></iframe>
            </div>
        </div>
        
        <main>
"""
    return head


def generate_html_footer() -> str:
    """Generate HTML footer section with current date."""
    from datetime import datetime

    current_date = datetime.now().strftime("%B %-d, %Y")

    return (
        """        </main>
        <footer>
            <p>by <a href="https://github.com/jxnl/instructor">Instructor</a> | <a href="https://github.com/jxnl/instructor">GitHub</a> | <span style="color: #888; font-size: 0.9em;">Last updated: """
        + current_date
        + """</span></p>
        </footer>
    </div>
    <script>
        // Function to copy code to clipboard
        function copyCode(button) {
            const codeBlock = button.closest('.code').querySelector('pre');
            const code = codeBlock.textContent;
            copyToClipboard(code, button);
        }
        
        // Function to copy all Python code
        document.addEventListener('DOMContentLoaded', function() {
            const copyAllButton = document.getElementById('copy-all-python');
            if (copyAllButton) {
                copyAllButton.addEventListener('click', function() {
                    const allCodeElement = document.getElementById('all-python-code');
                    const code = allCodeElement.textContent;
                    copyToClipboard(code, copyAllButton);
                });
            }
        });
        
        // Shared function to copy text and show tooltip
        function copyToClipboard(text, element) {
            // For older browsers, fallback to textarea method
            if (!navigator.clipboard) {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';  // Avoid scrolling to bottom
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    showTooltip(element, 'Copied!');
                } catch (err) {
                    console.error('Failed to copy text: ', err);
                    showTooltip(element, 'Error!');
                }
                
                document.body.removeChild(textArea);
                return;
            }
            
            // Use clipboard API if available
            navigator.clipboard.writeText(text).then(() => {
                showTooltip(element, 'Copied!');
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                showTooltip(element, 'Error!');
            });
        }
        
        // Helper to show tooltip
        function showTooltip(element, message) {
            // Check if there's already a tooltip
            let tooltip = element.parentElement.querySelector('.tooltip');
            if (tooltip) {
                tooltip.textContent = message;
            } else {
                // Create and append new tooltip
                tooltip = document.createElement('span');
                tooltip.textContent = message;
                tooltip.className = 'tooltip';
                tooltip.style.position = 'absolute';
                tooltip.style.background = '#333';
                tooltip.style.color = 'white';
                tooltip.style.padding = '2px 8px';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.top = '-25px';
                tooltip.style.right = '0';
                
                // Make sure the parent has position relative for tooltip positioning
                if (getComputedStyle(element.parentElement).position === 'static') {
                    element.parentElement.style.position = 'relative';
                }
                
                element.parentElement.appendChild(tooltip);
            }
            
            // Remove tooltip after 1.5 seconds
            setTimeout(() => tooltip.remove(), 1500);
        }

        // Enable keyboard navigation between examples
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) {
                return;
            }
            
            if (e.key === 'ArrowRight') {
                const nextLink = document.querySelector('.next a');
                if (nextLink) {
                    window.location.href = nextLink.getAttribute('href');
                }
            }
            
            if (e.key === 'ArrowLeft') {
                const prevLink = document.querySelector('.prev a');
                if (prevLink) {
                    window.location.href = prevLink.getAttribute('href');
                }
            }
        });
    </script>
</body>
</html>
"""
    )


def generate_index_html(
    examples: List[Dict[str, Any]], sections: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Generate index.html page with section grouping."""
    logger.info(
        "Generating index page with %d examples and %d sections"
        % (len(examples), len(sections))
    )

    output_file = output_dir / "index.html"
    with open(output_file, "w") as f:
        f.write(generate_html_head(
            SITE_TITLE, 
            base_url=".", 
            page_type="website", 
            canonical_path=""
        ))

        # Page content
        f.write(
            f"""
            <p style="margin: 20px 0; color: #444; line-height: 1.6;">
                A hands-on guide to structured data extraction from LLMs using <a href="https://github.com/jxnl/instructor" target="_blank">Instructor</a> 
                and <a href="https://docs.pydantic.dev/" target="_blank">Pydantic</a>.
            </p>
            <p style="margin: 20px 0; color: #444; line-height: 1.6;">
                Start with the <a href="{examples[0]["id"]}/">first example</a> 
                or browse below. Use arrow keys to navigate.
            </p>
            <p style="margin: 20px 0; color: #444; line-height: 1.6;">
                Requires Python <code>&gt;=3.9</code> and latest versions of Instructor and Pydantic.
            </p>
            <div style="margin-top: 20px;">
"""
        )

        # If we have sections defined, group examples by section
        if sections:
            # Group examples by section_id
            examples_by_section = {}
            for example in examples:
                section_id = example.get("section_id", "999-misc")
                if section_id not in examples_by_section:
                    examples_by_section[section_id] = []
                examples_by_section[section_id].append(example)

            # Display sections and their examples
            for section in sorted(sections, key=lambda s: s["order"]):
                section_examples = examples_by_section.get(section["id"], [])
                if not section_examples:
                    continue

                # Section header
                f.write(
                    f"""                <h3 style="margin-top: 25px; margin-bottom: 10px; color: #333; font-size: 1.3em;">{section["title"]}</h3>
"""
                )
                # Only include description paragraph if it's not empty
                description = section.get("description", "")
                if description:
                    f.write(
                        f"""                <p style="margin: 0 0 10px 0; color: #555; font-size: 0.9em;">{description}</p>
"""
                    )

                # Example links for this section
                for example in sorted(section_examples, key=lambda e: e["order"]):
                    f.write(
                        f"""                <div class="example-link">
                        <a href="{example["id"]}/">{example["title"]}</a>
                    </div>
"""
                    )
        else:
            # Fallback to flat list if no sections
            for example in examples:
                f.write(
                    f"""                <div class="example-link">
                        <a href="{example["id"]}/">{example["title"]}</a>
                    </div>
"""
                )

        f.write("            </div>\n")
        f.write(generate_html_footer())

    logger.info("Generated index page at %s" % output_file)


def copy_example_images(
    example: Dict[str, Any], project_root: Path, output_dir: Path
) -> None:
    """
    Copy images from the example directory to the output directory.

    Args:
        example: The example data
        project_root: Project root path
        output_dir: Output directory for the example
    """
    image_data = example.get("image_data", [])
    if not image_data:
        return

    # Create images directory in the example output directory
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True, parents=True)

    # Copy each image
    for image in image_data:
        src_path = project_root / image["path"]
        dst_path = images_dir / image["filename"]

        if src_path.exists():
            try:
                shutil.copy2(src_path, dst_path)
                logger.info(f"Copied image {src_path} to {dst_path}")
            except Exception as e:
                logger.error(f"Failed to copy image {src_path}: {e}")
        else:
            logger.warning(f"Image file not found: {src_path}")


def generate_example_html(
    example: Dict[str, Any], examples: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Generate an individual example page."""
    logger.info(
        "Generating page for example: %s - %s" % (example["id"], example["title"])
    )

    # Create directory for example
    example_dir = output_dir / example["id"]
    example_dir.mkdir(exist_ok=True, parents=True)

    # Copy images if any
    script_dir = Path(__file__).parent
    copy_example_images(example, script_dir, example_dir)

    # Create index.html in the example directory
    output_file = example_dir / "index.html"

    # Find the next and previous examples
    next_example = find_next_example(examples, example)
    prev_example = find_prev_example(examples, example)
    
    # Extract description from example
    page_description = example.get("description", SITE_DESCRIPTION)
    
    # Only use first sentence of description if it's too long
    if len(page_description) > 160:
        first_sentence = page_description.split(". ")[0] + "."
        page_description = first_sentence
        
    # Build canonical path
    canonical_path = f"{example['id']}/"

    with open(output_file, "w") as f:
        f.write(generate_html_head(
            f"{example['title']} - {SITE_TITLE}", 
            base_url="..",
            description=page_description,
            page_type="article",
            canonical_path=canonical_path,
            example_data=example
        ))

        # Collect all Python code for the "Copy All" button first
        all_python_code = ""
        for segment in example["code_segments"]:
            code_text = segment.get("display_code", "").strip()
            if code_text:
                all_python_code += code_text + "\n"

        # Section and page title with "Copy All" button
        section_title = example.get("section_title", "")

        # Header container with flexbox to position title and button
        f.write(
            """            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                <div>
"""
        )

        # Title part
        if section_title:
            f.write(
                f"""                    <div style="margin-bottom: 10px; color: #666; font-size: 0.9em;">
                        <a href="../" style="text-decoration: none; color: #666;">{section_title}</a>
                    </div>
                    <h1 style="margin: 0; margin-bottom: 10px;">{example["title"]}</h1>
"""
            )
        else:
            f.write(
                f"""                    <h1 style="margin: 0; margin-bottom: 10px;">{example["title"]}</h1>
"""
            )

        f.write(
            """                </div>
"""
        )

        # Button part (if we have Python code)
        if all_python_code:
            # GitHub edit URL - extract the base name from the example ID (after the dash)
            example_id_parts = example["id"].split("-", 1)
            python_filename = (
                example_id_parts[1] if len(example_id_parts) > 1 else example["id"]
            )
            github_edit_url = f"https://github.com/jxnl/structuredoutputsbyexample/edit/main/examples/{example['id']}/{python_filename}.py"

            f.write(
                """                <div style="position: relative; margin-top: 10px; display: flex; gap: 8px;">
                    <button id="copy-all-python" style="background-color: #f1f8ff; border: 1px solid #c8e1ff; border-radius: 6px; padding: 6px 12px; font-size: 14px; color: #0066CC; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM19 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H19C20.1 23 21 22.1 21 21V7C21 5.9 20.1 5 19 5ZM19 21H8V7H19V21Z" fill="currentColor"/>
                        </svg>
                        Copy All Python
                    </button>"""
                + f"""
                    <a href="{github_edit_url}" target="_blank" style="background-color: #f6f1ff; border: 1px solid #d8c9f7; border-radius: 6px; padding: 6px 12px; font-size: 14px; color: #6f42c1; text-decoration: none; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" fill="currentColor"/>
                        </svg>
                        Edit
                    </a>
                    <div id="all-python-code" style="display: none;">{escape(all_python_code)}</div>
                </div>"""
            )

        # Close header container
        f.write(
            """            </div>
"""
        )

        # Description if available
        if example.get("description"):
            # Replace newlines with <br> tags to preserve formatting
            formatted_description = example["description"].replace("\n", "<br>")
            f.write(
                f"""            <p style="margin: 20px 0 40px 0; color: #444; line-height: 1.6; font-size: 1.1em; white-space: pre-line;">
                {formatted_description}
            </p>
"""
            )

        # Group segments by section headers
        sections = []
        current_section = None
        current_segments = []

        for segment in example["code_segments"]:
            annotation = segment.get("annotation", "")
            code_text = segment.get("display_code", "").strip()

            # Skip completely empty segments
            if not annotation and not code_text:
                continue

            # If annotation with no code, it's a section header
            if annotation and not code_text:
                # Add previous section if exists
                if current_section:
                    sections.append(
                        {"header": current_section, "segments": current_segments}
                    )

                # Start a new section
                current_section = annotation
                current_segments = []
            else:
                # Add to current section
                current_segments.append(segment)

        # Add the final section
        if current_section and current_segments:
            sections.append({"header": current_section, "segments": current_segments})

        # Process each section
        for i, section in enumerate(sections):
            # Add divider if not first section
            if i > 0:
                f.write(
                    """            <hr>
"""
                )

            # Process segments in this section
            for segment in section["segments"]:
                combined_annotation = ""
                if section["header"]:
                    # Replace newlines with <br> tags in section header
                    header_with_breaks = section["header"].replace("\n", "<br>")
                    combined_annotation += f"<div style='font-size: 0.9em; color: #666;'>{header_with_breaks}</div>\n"

                annotation = segment.get("annotation", "")
                if annotation:
                    # Replace newlines with <br> tags to preserve formatting
                    annotation = annotation.replace("\n", "<br>")
                    combined_annotation += annotation

                code_text = segment.get("display_code", "").strip()

                # If there's no code or annotation, skip
                if not code_text and not combined_annotation:
                    continue

                # Start row
                f.write(
                    """            <div class="row">
"""
                )

                # Left column (annotation)
                if combined_annotation:
                    f.write(
                        f"""                <div class="docs">
                    {combined_annotation}
                </div>
"""
                    )

                # Right column (code) - without individual copy buttons
                if code_text:
                    f.write(
                        f"""                <div class="code">
                    <pre><code class="language-python">{escape(code_text)}</code></pre>
                </div>
"""
                    )

                # End row
                f.write(
                    """            </div>
"""
                )

        # Shell segments if available
        shell_segments = example.get("shell_segments", [])
        if shell_segments:
            f.write(
                """            <hr>
            <h2>Running the Example</h2>
"""
            )

            for segment in shell_segments:
                explanation = segment.get("explanation", "")
                # Replace newlines with <br> tags to preserve formatting in explanations
                if explanation:
                    explanation = explanation.replace("\n", "<br>")
                command = segment.get("command", "")
                output = segment.get("output", "")

                f.write(
                    """            <div class="row">
"""
                )

                # Left column (explanation)
                if explanation:
                    f.write(
                        f"""                <div class="docs" style='font-size: 0.9em; color: #666;'>
                    {escape(explanation)}
                </div>
"""
                    )

                # Right column (command + output)
                f.write(
                    f"""                <div class="code">
                    <div class="buttons">
                        <svg class="copy" title="Copy command" onclick="copyCode(this)" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM19 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H19C20.1 23 21 22.1 21 21V7C21 5.9 20.1 5 19 5ZM19 21H8V7H19V21Z" fill="currentColor"/>
                        </svg>
                    </div>
                    <pre><code class="language-shell"><span><span class="command-prompt">$ </span><span class="command-text">{escape(command)}</span></span>
{escape(output)}</code></pre>
                </div>
"""
                )

                f.write(
                    """            </div>
"""
                )

        # Images section if available
        image_data = example.get("image_data", [])
        if image_data:
            f.write(
                """            <hr>
"""
            )

            for image in image_data:
                filename = image.get("filename", "")

                # Create a figure with the image
                f.write(
                    f"""            <div style="margin: 30px 0; text-align: center;">
                <figure>
                    <img src="images/{filename}" alt="An illustration or output
                    from the example code" style="max-width: 100%; border: 1px solid #eee;
                    border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <figcaption style="margin-top: 10px; color: #666; font-style: italic;"></figcaption>
                </figure>
            </div>
"""
                )

        # Documentation links section if available
        documentation_links = example.get("documentation_links", [])
        if documentation_links:
            f.write(
                """            <hr>
            <h4>Further Information</h4>
            <ul style="font-size: 0.9em;">
"""
            )
            for i, link in enumerate(documentation_links, 1):
                f.write(
                    f"""                <li><a href="{link}"
                         target="_blank">Documentation link {i}</a></li>
"""
                )
            f.write(
                """            </ul>
"""
            )

        # Navigation links
        f.write(
            """            <div class="navigation">
"""
        )

        # Previous example link
        if prev_example:
            f.write(
                f"""                <p class="prev">
                    <span>← Previous:</span> <a href="../{prev_example["id"]}/">{prev_example["title"]}</a>
                </p>
"""
            )

        # Next example link
        if next_example:
            f.write(
                f"""                <p class="next">
                    <span>Next:</span> <a href="../{next_example["id"]}/">{next_example["title"]}</a> →
                </p>
"""
            )

        f.write(
            """            </div>
"""
        )

        f.write(generate_html_footer())

    logger.info("Generated example page at %s" % output_file)


def copy_static_files(source_dir: Path, output_dir: Path) -> None:
    """Copy static files to the output directory."""
    target_dir = output_dir / "static"

    # Create target directory
    target_dir.mkdir(exist_ok=True, parents=True)

    # Copy static files
    if source_dir.exists():
        logger.info("Copying static files from %s to %s" % (source_dir, target_dir))
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    else:
        logger.warning("Static directory %s does not exist" % source_dir)


def extract_code_from_example(example: Dict[str, Any]) -> str:
    """Extract all Python code from an example's code segments."""
    code = ""
    for segment in example.get("code_segments", []):
        if segment.get("display_code", "").strip():
            code += segment.get("display_code", "").strip() + "\n"
    return code.strip()


def extract_shell_from_example(example: Dict[str, Any]) -> str:
    """Extract shell commands and outputs from an example."""
    shell = ""
    for segment in example.get("shell_segments", []):
        cmd = segment.get("command", "").strip()
        out = segment.get("output", "").strip()
        if cmd:
            shell += f"$ {cmd}\n"
            if out:
                shell += f"{out}\n"
    return shell.strip()


def generate_llms_ctx_txt(
    examples: List[Dict[str, Any]], sections: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Generate llms-ctx.txt file with organized headers and full example code."""
    logger.info("Generating llms-ctx.txt")

    output_file = output_dir / "llms-ctx.txt"

    # Group examples by section
    examples_by_section = {}
    for example in examples:
        section_id = example.get("section_id", "999-misc")
        if section_id not in examples_by_section:
            examples_by_section[section_id] = []
        examples_by_section[section_id].append(example)

    with open(output_file, "w") as f:
        # Main heading and introduction
        f.write("# Structured Outputs by Example\n\n")
        f.write(
            "This file contains all examples from the Structured Outputs by Example site.\n"
        )
        f.write(
            "It's organized by sections, with each example's Python code and terminal commands included.\n\n"
        )

        # Table of contents
        f.write("## Table of Contents\n\n")
        for section in sorted(sections, key=lambda s: s["order"]):
            section_examples = examples_by_section.get(section["id"], [])
            if not section_examples:
                continue

            f.write(f"* {section['title']}\n")
            for example in sorted(section_examples, key=lambda e: e["order"]):
                f.write(f"  * {example['title']}\n")
        f.write("\n")

        # Each section with its examples
        for section in sorted(sections, key=lambda s: s["order"]):
            section_examples = examples_by_section.get(section["id"], [])
            if not section_examples:
                continue

            # Section heading
            f.write(f"## {section['title']}\n\n")

            # Section description if available
            if section.get("description"):
                f.write(f"{section['description']}\n\n")

            # Each example in the section
            for example in sorted(section_examples, key=lambda e: e["order"]):
                # Example heading
                f.write(f"### {example['title']}\n\n")

                # Example description if available
                if example.get("description"):
                    f.write(f"{example['description']}\n\n")

                # Python code
                python_code = extract_code_from_example(example)
                if python_code:
                    f.write("```python\n")
                    f.write(python_code)
                    f.write("\n```\n\n")

                # Shell commands and output
                shell_code = extract_shell_from_example(example)
                if shell_code:
                    f.write("```shell\n")
                    f.write(shell_code)
                    f.write("\n```\n\n")

                # Image references if any
                if example.get("image_data"):
                    f.write(
                        "*This example includes images which can be viewed on the website.*\n\n"
                    )

                # Documentation links if any
                documentation_links = example.get("documentation_links", [])
                if documentation_links:
                    f.write("For more information, see the original documentation:\n")
                    for link in documentation_links:
                        f.write(f"- {link}\n")
                    f.write("\n")

    logger.info(f"Generated llms-ctx.txt at {output_file}")


def generate_llms_txt(
    examples: List[Dict[str, Any]], sections: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Generate llms.txt file with simplified content and links to examples."""
    logger.info("Generating simplified llms.txt")

    output_file = output_dir / "llms.txt"

    # Group examples by section
    examples_by_section = {}
    for example in examples:
        section_id = example.get("section_id", "999-misc")
        if section_id not in examples_by_section:
            examples_by_section[section_id] = []
        examples_by_section[section_id].append(example)

    with open(output_file, "w") as f:
        # Main heading and introduction
        f.write("# Structured Outputs by Example\n\n")
        f.write(
            "> Structured Outputs by Example is a hands-on introduction to working with structured data extraction from LLMs. "
            "The site showcases how to use libraries like [Instructor](https://github.com/jxnl/instructor) "
            "and [Pydantic](https://docs.pydantic.dev/) to reliably extract structured information from LLM outputs.\n\n"
        )
        f.write(
            "Examples here assume Python `>=3.9` and "
            "the latest versions of Instructor and Pydantic. "
            "Try to upgrade to the latest versions if something isn't working.\n\n"
        )
        f.write(
            "Note: A more comprehensive version of this file / documentation is available at "
            "llms-ctx.txt, "
            "which contains the full text of all examples including code samples and terminal output. "
            "You could paste that into your IDE or AI model to then ask "
            "questions and get it to generate code with the examples as context.\n\n"
        )

        # Each section with its examples
        for section in sorted(sections, key=lambda s: s["order"]):
            section_examples = examples_by_section.get(section["id"], [])
            if not section_examples:
                continue

            # Section heading
            f.write(f"## {section['title']}\n\n")

            # Each example in the section as a bullet point
            for example in sorted(section_examples, key=lambda e: e["order"]):
                f.write(f"- {example['title']}")
                if example.get("description"):
                    # Format multi-line descriptions with proper indentation
                    desc_lines = example["description"].split("\n")
                    # Add first line after the title
                    f.write(f": {desc_lines[0]}")
                    # Add remaining lines with proper indentation
                    if len(desc_lines) > 1:
                        f.write("\n")
                        for line in desc_lines[1:]:
                            f.write(f"  {line}\n")
                    # No need for extra newline since we're already adding them properly
                else:
                    f.write("\n")
            f.write("\n")

        # Add footer information
        from datetime import datetime

        current_date = datetime.now().strftime("%B %-d, %Y")

        f.write("## Resources\n\n")
        f.write("- [Instructor GitHub](https://github.com/jxnl/instructor)\n")
        f.write(
            "- [Instructor Documentation](https://instructor-ai.github.io/instructor/)\n"
        )
        f.write("- [Pydantic Documentation](https://docs.pydantic.dev/)\n\n")
        f.write(f"Last updated: {current_date}\n")

    logger.info(f"Generated simplified llms.txt at {output_file}")


def clean_docs_directory(output_dir: Path) -> None:
    """
    Clean up old files and example directories in the docs directory.

    Preserves important files like CNAME, .nojekyll, etc.

    Args:
        output_dir: Path to the docs directory
    """
    logger.info("Cleaning up old example directories and files in %s" % output_dir)

    # Files to preserve (never delete these)
    preserve_files = {
        "CNAME",  # Custom domain configuration
        ".nojekyll",  # GitHub Pages configuration
        ".gitignore",  # Git ignore file
    }

    # Directories to preserve (never delete these)
    preserve_dirs = {"static"}  # Static assets directory

    # Remove index.html
    index_file = output_dir / "index.html"
    if index_file.exists():
        index_file.unlink()
        logger.info("Removed %s" % index_file)

    # Remove llms.txt and llms-ctx.txt
    llms_file = output_dir / "llms.txt"
    if llms_file.exists():
        llms_file.unlink()
        logger.info("Removed %s" % llms_file)

    llms_ctx_file = output_dir / "llms-ctx.txt"
    if llms_ctx_file.exists():
        llms_ctx_file.unlink()
        logger.info("Removed %s" % llms_ctx_file)

    # Remove all example directories (folders that match the pattern \d{3}-*)
    for item in output_dir.iterdir():
        if item.is_dir() and item.name not in preserve_dirs:
            # Check if it's an example directory (matches pattern 001-*, 002-*, etc.)
            if re.match(r"^\d{3}-", item.name):
                shutil.rmtree(item)
                logger.info("Removed directory %s" % item)


def generate_sitemap(
    examples: List[Dict[str, Any]], sections: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Generate sitemap.xml file for search engines.
    
    Args:
        examples: List of examples data
        sections: List of sections data
        output_dir: Output directory for the site
    """
    from datetime import datetime
    
    logger.info("Generating sitemap.xml")
    
    site_url = "https://structuredoutputsbyexample.com"
    today = datetime.now().strftime("%Y-%m-%d")
    
    output_file = output_dir / "sitemap.xml"
    
    with open(output_file, "w") as f:
        # XML header
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        
        # Homepage
        f.write('  <url>\n')
        f.write(f'    <loc>{site_url}</loc>\n')
        f.write(f'    <lastmod>{today}</lastmod>\n')
        f.write('    <changefreq>weekly</changefreq>\n')
        f.write('    <priority>1.0</priority>\n')
        f.write('  </url>\n')
        
        # Example pages
        for example in examples:
            f.write('  <url>\n')
            f.write(f'    <loc>{site_url}/{example["id"]}/</loc>\n')
            f.write(f'    <lastmod>{today}</lastmod>\n')
            f.write('    <changefreq>monthly</changefreq>\n')
            f.write('    <priority>0.8</priority>\n')
            f.write('  </url>\n')
        
        # Close urlset
        f.write('</urlset>\n')
    
    logger.info(f"Generated sitemap at {output_file}")


def generate_robots_txt(output_dir: Path) -> None:
    """Generate robots.txt file for search engines.
    
    Args:
        output_dir: Output directory for the site
    """
    logger.info("Generating robots.txt")
    
    output_file = output_dir / "robots.txt"
    
    with open(output_file, "w") as f:
        f.write("User-agent: *\n")
        f.write("Allow: /\n\n")
        f.write("Sitemap: https://structuredoutputsbyexample.com/sitemap.xml\n")
    
    logger.info(f"Generated robots.txt at {output_file}")


def generate_static_site() -> None:
    """Generate the complete static site."""
    data = load_examples_data()
    examples = data.get("examples", [])
    sections = data.get("sections", [])

    if not examples:
        logger.error("No examples found. Exiting.")
        return

    script_dir = Path(__file__).parent
    output_dir = script_dir / "docs"
    static_dir = script_dir / "static"

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    logger.info("Generating static site in %s" % output_dir)

    # Clean up old files and directories
    clean_docs_directory(output_dir)

    # Copy static files
    copy_static_files(static_dir, output_dir)

    # Generate llms-ctx.txt file (original format with full examples)
    generate_llms_ctx_txt(examples, sections, output_dir)

    # Generate llms.txt file (simplified format with links)
    generate_llms_txt(examples, sections, output_dir)

    # Generate index page
    generate_index_html(examples, sections, output_dir)

    # Generate example pages
    for example in examples:
        generate_example_html(example, examples, output_dir)
    
    # Generate SEO files
    generate_sitemap(examples, sections, output_dir)
    generate_robots_txt(output_dir)

    logger.info(
        "Static site generation complete! The site is available at %s" % output_dir
    )


if __name__ == "__main__":
    # First run the examples builder by importing it directly
    logger.info("Running examples builder first...")
    import sys

    # Add the build_examples directory to sys.path if needed
    build_examples_dir = Path(__file__).parent / "build_examples"
    if str(build_examples_dir) not in sys.path:
        sys.path.append(str(build_examples_dir))

    # Import and run the main function from build_examples
    try:
        from build_examples import main as build_examples_main

        build_examples_main()
    except Exception as e:
        logger.error(f"Error running build_examples: {e}")
        logger.warning("Continuing with static site generation...")

    # Then generate the static site
    generate_static_site()

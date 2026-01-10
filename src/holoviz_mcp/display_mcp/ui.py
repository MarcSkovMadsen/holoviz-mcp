"""Shared UI components for the Display Server."""

import panel as pn


# A UI component to put in the FastListTemplate header. To inform users that this is alpha/experimental software.
def banner():
    """Create a banner indicating alpha/experimental software."""
    banner_html = """
    <div style="background-color: #ffcc00; color: #1a1a1a; padding: 12px 20px; text-align: center; \
font-weight: bold; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <span style="font-size: 1.3em;">⚠️</span>
        <strong>Alpha Release:</strong> This is experimental software for testing and exploration only.
        <span style="font-size: 1.3em;">⚠️</span>
    </div>
    """
    return pn.pane.HTML(banner_html, align="center", styles={"margin-left": "auto", "margin-right": "auto"})

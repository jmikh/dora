#!/usr/bin/env python3
"""
Create a standalone dashboard HTML file with embedded data
"""

import json
from pathlib import Path


def create_standalone_dashboard():
    """
    Create a single HTML file with embedded JSON data
    """
    script_dir = Path(__file__).parent

    # Read the dashboard HTML
    html_file = script_dir / "dashboard.html"
    with open(html_file, 'r') as f:
        html_content = f.read()

    # Read the JSON data
    json_file = script_dir / "dashboard_data.json"
    with open(json_file, 'r') as f:
        json_data = f.read()

    # Replace the fetch call with embedded data
    old_code = """        // Load dashboard data
        async function loadDashboard() {
            try {
                const response = await fetch('dashboard_data.json');
                dashboardData = await response.json();
                renderDashboard();
            } catch (error) {
                console.error('Error loading dashboard:', error);
                document.querySelector('.chart-container').innerHTML =
                    '<div class="loading" style="color: #e53e3e;">Error loading data. Please run generate_dashboard_data.py first.</div>';
            }
        }"""

    new_code = f"""        // Embedded dashboard data
        const embeddedData = {json_data};

        // Load dashboard data
        function loadDashboard() {{
            try {{
                dashboardData = embeddedData;
                renderDashboard();
            }} catch (error) {{
                console.error('Error loading dashboard:', error);
                document.querySelector('.chart-container').innerHTML =
                    '<div class="loading" style="color: #e53e3e;">Error loading data.</div>';
            }}
        }}"""

    # Replace in HTML
    standalone_html = html_content.replace(old_code, new_code)

    # Save standalone version
    output_file = script_dir / "dashboard_standalone.html"
    with open(output_file, 'w') as f:
        f.write(standalone_html)

    print("✅ Created standalone dashboard: dashboard_standalone.html")
    print(f"   Size: {output_file.stat().st_size / 1024:.1f} KB")
    print()
    print("This file can be:")
    print("  - Double-clicked to open in any browser")
    print("  - Shared via email/Slack")
    print("  - Opened from any location")
    print("  - No external dependencies needed!")


if __name__ == "__main__":
    create_standalone_dashboard()

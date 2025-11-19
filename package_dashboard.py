#!/usr/bin/env python3
"""
Package the dashboard for sharing as static files
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime


def package_dashboard(create_zip: bool = True, output_dir: str = "dashboard_package"):
    """
    Package dashboard files for sharing

    Args:
        create_zip: Whether to create a ZIP file
        output_dir: Output directory name
    """
    script_dir = Path(__file__).parent
    package_dir = script_dir / output_dir

    print("📦 Packaging Wispr Flow Dashboard for sharing...")
    print()

    # First, create standalone version with embedded data
    print("🔧 Creating standalone version with embedded data...")
    import subprocess
    result = subprocess.run([sys.executable, "create_standalone_dashboard.py"],
                          capture_output=True, text=True, cwd=script_dir)
    if result.returncode == 0:
        print("   ✅ Standalone dashboard created")
    else:
        print("   ⚠️  Warning: Could not create standalone version")
        print(f"   {result.stderr}")

    # Create package directory
    if package_dir.exists():
        print(f"🗑️  Removing existing package directory...")
        shutil.rmtree(package_dir)

    package_dir.mkdir()
    print(f"📁 Created package directory: {output_dir}/")

    # Copy standalone dashboard (with embedded data)
    src = script_dir / "dashboard_standalone.html"
    if src.exists():
        # Copy as dashboard.html (simpler name for user)
        shutil.copy2(src, package_dir / "dashboard.html")
        print(f"   ✅ Copied dashboard.html (standalone with embedded data)")
    else:
        print(f"   ⚠️  Warning: dashboard_standalone.html not found")

    # Logo is now text-based, no image needed
    print(f"   ℹ️  Using text logo (no image file needed)")

    # Create README
    readme_content = """# Wispr Flow Insights Dashboard

## How to View

1. Extract all files from this folder (if zipped)
2. Double-click `dashboard.html` to open in your browser
3. That's it! The dashboard will load automatically

## Requirements

- Any modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection ONLY for first load (downloads Chart.js library)
- After first load, works completely offline
- No installation needed

## What You'll See

- Interactive stacked bar chart showing pain points over time
- 7 color-coded clusters of issues
- Click any bar or legend item to see detailed pain points
- Use cases grid showing how users leverage Wispr Flow
- Click to see original review context

## Data Snapshot

This dashboard contains a snapshot of Wispr Flow review insights:
- 295 total reviews analyzed
- 80 clustered pain points
- 116 use cases
- Timeline: July 2025 - November 2025

Generated: {timestamp}

## Troubleshooting

**Dashboard won't load?**
- Make sure both `dashboard.html` and `dashboard_data.json` are in the same folder
- Try a different browser (recommend Chrome or Firefox)
- Check that JavaScript is enabled in your browser

**Charts not showing?**
- You need an internet connection for the first load (to download Chart.js library)
- After first load, it works offline

**Need help?**
Contact the person who sent you this dashboard.

---

Powered by Claude Code & Chart.js
"""

    readme_path = package_dir / "README.txt"
    with open(readme_path, 'w') as f:
        f.write(readme_content.format(timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")))
    print(f"   ✅ Created README.txt")

    print()
    print(f"✅ Package created successfully in: {output_dir}/")
    print()
    print("📂 Package contents:")
    for item in package_dir.iterdir():
        size = item.stat().st_size
        size_kb = size / 1024
        print(f"   - {item.name} ({size_kb:.1f} KB)")

    # Create ZIP file
    if create_zip:
        print()
        print("🗜️  Creating ZIP file...")
        zip_filename = f"{output_dir}.zip"
        zip_path = script_dir / zip_filename

        # Remove existing zip
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(script_dir)
                    zipf.write(file_path, arcname)
                    print(f"   ✅ Added {arcname}")

        zip_size = zip_path.stat().st_size / 1024
        print()
        print(f"✅ ZIP file created: {zip_filename} ({zip_size:.1f} KB)")
        print()
        print("📧 Ready to share!")
        print()
        print("You can now:")
        print(f"   1. Send {zip_filename} to your friend via email/Slack/etc")
        print(f"   2. Or share the {output_dir}/ folder directly")
        print()
        print("Your friend just needs to:")
        print("   1. Extract the ZIP file")
        print("   2. Double-click dashboard.html")
        print("   3. Enjoy the interactive dashboard! 🎉")
    else:
        print()
        print("📧 Ready to share!")
        print()
        print(f"Share the {output_dir}/ folder with your friend.")
        print("They can double-click dashboard.html to view it.")

    print()
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Package dashboard files for sharing"
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Don't create a ZIP file, just the folder"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="dashboard_package",
        help="Output directory name (default: dashboard_package)"
    )

    args = parser.parse_args()

    package_dashboard(
        create_zip=not args.no_zip,
        output_dir=args.output
    )

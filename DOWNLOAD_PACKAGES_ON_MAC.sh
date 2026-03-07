#!/bin/bash
# ================================================================
#  DOWNLOAD_PACKAGES_ON_MAC.sh
#  Run this on your Mac (with internet) ONCE.
#  It downloads all Python packages needed for the Windows server.
#  Then copy the 'packages' folder to USB and paste it next to
#  SETUP.bat on the Windows server.
# ================================================================

echo ""
echo "================================================"
echo "  Limited Tender Manager — Package Downloader"
echo "  Run on Mac with internet. Copy result to USB."
echo "================================================"
echo ""

# Go to the folder where this script lives
cd "$(dirname "$0")"

# Create packages folder
mkdir -p packages

echo "Downloading packages for Windows (64-bit)..."
echo "This needs internet and takes 2-3 minutes."
echo ""

# Download wheels for Windows 64-bit Python 3.11/3.12/3.13
# --platform and --python-version ensure we get Windows-compatible files
pip3 download \
    flask \
    flask-cors \
    psycopg2-binary \
    werkzeug \
    --dest ./packages \
    --platform win_amd64 \
    --python-version 311 \
    --only-binary=:all: \
    --no-deps 2>/dev/null

# Also download for Python 3.12 in case server has that version
pip3 download \
    flask \
    flask-cors \
    psycopg2-binary \
    werkzeug \
    --dest ./packages \
    --platform win_amd64 \
    --python-version 312 \
    --only-binary=:all: \
    --no-deps 2>/dev/null

# Also download pure-python packages (work on any version)
pip3 download \
    flask \
    flask-cors \
    werkzeug \
    click \
    itsdangerous \
    jinja2 \
    markupsafe \
    blinker \
    --dest ./packages \
    --no-binary=:none: \
    --no-deps 2>/dev/null

# Download with dependencies (catches everything)
pip3 download \
    flask \
    flask-cors \
    psycopg2-binary \
    werkzeug \
    --dest ./packages

echo ""
echo "================================================"
echo "  DONE!"
echo "================================================"
echo ""
echo "  A 'packages' folder was created here:"
echo "  $(pwd)/packages"
echo ""
echo "  Copy that entire 'packages' folder to USB drive."
echo ""
echo "  On the Windows server:"
echo "    1. Paste 'packages' folder next to SETUP.bat"
echo "    2. Run SETUP.bat"
echo ""
echo "  Files in packages:"
ls packages/ | wc -l
echo "  packages downloaded."
echo ""

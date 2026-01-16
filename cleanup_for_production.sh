#!/bin/bash
# cleanup_for_production.sh
# Prepares chessdotcomcoach production repository

set -e  # Exit on error

echo "🧹 Cleaning up for production repository: chessdotcomcoach"
echo ""

# ============================================================================
# STEP 1: Remove experimental/one-off scripts
# ============================================================================
echo "📝 Removing experimental scripts..."

rm -f debug_tactical.py
rm -f fix_tactical_analyzer.py
rm -f quick_tactical_fix.py
rm -f tactical_analysis_cell.py
rm -f test_username.py  # Will consolidate into main test

echo "✅ Removed 5 experimental scripts"

# ============================================================================
# STEP 2: Clean up notebooks - keep only essential ones
# ============================================================================
echo ""
echo "📓 Organizing notebooks..."

# Create archive directory
mkdir -p notebooks/archive

# Archive redundant tactical review (keep simple version)
git mv notebooks/tactical_review.ipynb notebooks/archive/ 2>/dev/null || mv notebooks/tactical_review.ipynb notebooks/archive/

# Remove Jupyter checkpoints
rm -rf notebooks/.ipynb_checkpoints

echo "✅ Archived 1 redundant notebook"

# ============================================================================
# STEP 3: Consolidate documentation
# ============================================================================
echo ""
echo "📚 Consolidating documentation..."

# Archive overly detailed docs (will replace with concise README)
mkdir -p docs/archive
git mv docs/ARCHITECTURE.md docs/archive/ 2>/dev/null || mv docs/ARCHITECTURE.md docs/archive/
git mv docs/IMPLEMENTATION_GUIDE.md docs/archive/ 2>/dev/null || mv docs/IMPLEMENTATION_GUIDE.md docs/archive/
git mv docs/PROJECT_SUMMARY.md docs/archive/ 2>/dev/null || mv docs/PROJECT_SUMMARY.md docs/archive/
git mv docs/TECHNICAL_SPECS.md docs/archive/ 2>/dev/null || mv docs/TECHNICAL_SPECS.md docs/archive/

# Keep CHANGELOG for history, archive QUICK_START (will merge into README)
git mv QUICK_START.md docs/archive/ 2>/dev/null || mv QUICK_START.md docs/archive/

echo "✅ Archived 5 documentation files (available in docs/archive/)"

# ============================================================================
# STEP 4: Clean test structure
# ============================================================================
echo ""
echo "🧪 Consolidating tests..."

# Keep test_basic_functionality.py as main test suite
# Remove redundant test_imports_only.py (covered in main suite)
rm -f tests/test_imports_only.py

# Consolidate test_app.py into tests directory
git mv test_app.py tests/test_integration.py 2>/dev/null || mv test_app.py tests/test_integration.py

echo "✅ Consolidated to 2 test files"

# ============================================================================
# STEP 5: Create .gitignore additions for clean repo
# ============================================================================
echo ""
echo "🚫 Updating .gitignore..."

cat >> .gitignore << 'EOF'

# Production-only ignores
docs/archive/
notebooks/archive/
*.pyc
__pycache__/
.pytest_cache/
.coverage
htmlcov/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter
.ipynb_checkpoints/
notebooks/data/  # Local notebook data

EOF

echo "✅ Updated .gitignore"

# ============================================================================
# STEP 6: Summary
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Removed:"
echo "  • 5 experimental scripts"
echo "  • 1 redundant notebook"
echo "  • 5 overly-detailed docs"
echo "  • 1 redundant test file"
echo ""
echo "Kept (Production-Ready):"
echo "  • src/ - Core analysis modules"
echo "  • notebooks/ - 4 essential notebooks"
echo "  • tests/ - 2 test files"
echo "  • config/ - Configuration"
echo "  • CHANGELOG.md - Version history"
echo ""
echo "Archived (for reference):"
echo "  • docs/archive/ - Original documentation"
echo "  • notebooks/archive/ - Old notebook versions"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Create new README: (we'll provide template)"
echo "  3. Commit: git commit -m 'Clean production-ready fork'"
echo "  4. Push: git push origin main"
echo ""

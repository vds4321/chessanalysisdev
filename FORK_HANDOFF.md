# Fork Creation Handoff - chessdotcomcoach

## Context
Creating production fork of chessanalysisdev → chessdotcomcoach
- **Production repo:** Clean, minimal, human-curated
- **Experimental repo (current):** LLM experiments, rapid iteration

## Files Created (Ready to Use)

### 1. Cleanup Script
**Location:** `cleanup_for_production.sh`
**Status:** ✅ Ready to run
**What it does:**
- Removes 5 experimental scripts (debug_tactical.py, fix_tactical_analyzer.py, etc.)
- Archives redundant notebook (tactical_review.ipynb)
- Consolidates docs to docs/archive/
- Cleans test structure
- Updates .gitignore

### 2. Production README
**Location:** `README_PRODUCTION.md`
**Status:** ⚠️ NEEDS TO BE CREATED (ran out of context)
**Template saved in conversation** - includes:
- Clear value proposition
- Quick start (actually works)
- Example outputs
- FAQ
- Simple architecture
- Human voice (not AI slop)

## Next Steps (Execute in Order)

### Step 1: Create GitHub Repo
```bash
# On GitHub:
# 1. New repository
# 2. Name: chessdotcomcoach
# 3. Description: "Analyze your Chess.com games and get actionable coaching insights"
# 4. Public
# 5. DO NOT initialize with README
```

### Step 2: Clone and Prepare
```bash
cd ~/Documents/GitHub
git clone https://github.com/vds4321/chessanalysisdev.git chessdotcomcoach
cd chessdotcomcoach

# Remove old remote, add new
git remote remove origin
git remote add origin https://github.com/vds4321/chessdotcomcoach.git

# Create cleanup branch
git checkout -b production-cleanup
```

### Step 3: Run Cleanup
```bash
chmod +x cleanup_for_production.sh
./cleanup_for_production.sh

# Review what changed
git status
```

### Step 4: Create Production README
```bash
# Copy template from README_PRODUCTION.md (need to create it)
# OR ask Claude to regenerate in fresh context
mv README.md README_ORIGINAL.md
# Create new README.md with production content
```

### Step 5: Commit and Push
```bash
git add -A
git commit -m "Initial production fork - clean, focused chess analysis

Removed experimental scripts and consolidated documentation.
This repository contains proven, working chess analysis tools.

Experimental work continues at: vds4321/chessanalysisdev"

git push -u origin production-cleanup
git checkout -b main
git merge production-cleanup
git push -u origin main
```

### Step 6: Update Experimental Repo
```bash
cd /Users/martinhynie/Documents/GitHub/chessanalysisdev

# Create EXPERIMENTS.md
# Update README to point to production fork
# Mark as experimental/development repo
```

## Key Decisions Made

1. **Name:** chessdotcomcoach (clear purpose)
2. **Strategy:** Fork now, experiment in original
3. **Philosophy:** Clean production + messy experiments
4. **First feature:** Single LLM skill POC (chess_coach.py ~100 lines)

## Files to Delete in Production Fork
- debug_tactical.py
- fix_tactical_analyzer.py
- quick_tactical_fix.py
- tactical_analysis_cell.py
- test_username.py
- docs/ARCHITECTURE.md (→ archive)
- docs/IMPLEMENTATION_GUIDE.md (→ archive)
- docs/PROJECT_SUMMARY.md (→ archive)
- docs/TECHNICAL_SPECS.md (→ archive)
- QUICK_START.md (→ archive, merge into README)
- notebooks/tactical_review.ipynb (→ archive, keep simple version)

## Files to Keep in Production Fork
**Core:**
- src/ (all analysis modules)
- config/settings.py
- requirements.txt

**Notebooks:**
- main_analysis.ipynb
- progression_analysis.ipynb
- tactical_review_simple.ipynb
- ml_recommender_demo.ipynb

**Tests:**
- tests/test_basic_functionality.py
- test_app.py → tests/test_integration.py

**Docs:**
- CHANGELOG.md
- README.md (NEW - production version)
- .env.example

## After Fork Complete - Next Phase

### Phase 1: LLM Proof of Concept (in experimental repo)
Create in chessanalysisdev (NOT chessdotcomcoach):

**File:** `src/llm/chess_coach.py` (~100 lines)
- Single class: SimpleChessCoach
- One method: explain_tactical_mistakes()
- Takes tactical_analysis dict → returns coaching string
- Uses Anthropic API
- No abstraction, no framework

**File:** `tests/test_chess_coach.py`
- Mock-based unit tests
- Optional integration test with real API

**File:** `notebooks/llm_coaching_demo.ipynb`
- Demonstrates LLM coaching on real games
- Documents if it actually helps chess
- Basis for promotion to production

**File:** `LEARNINGS.md`
- What worked, what didn't
- Chess value assessment
- Next experiments

### Success Criteria for Promotion to Production
1. ✅ Code is <150 lines and obvious
2. ✅ Actually improves chess understanding (not generic advice)
3. ✅ Tests prove it works
4. ✅ Documentation explains value

## Resume Point
When continuing in new context:
1. Ask Claude to read this handoff
2. Generate production README from template
3. Execute Steps 1-6 above
4. Move to Phase 1 (LLM POC in experimental)

## Template Snippets Saved

### Production README Structure
- What This Does (clear value prop)
- Quick Start (copy-paste friendly)
- Example Output (screenshots)
- How It Works (simple diagram)
- Project Structure (tree)
- Requirements
- Notebooks Guide
- Example Analysis (real results)
- FAQ
- Development
- Roadmap (realistic)
- Credits
- License

### EXPERIMENTS.md Structure (for experimental repo)
- Active Experiments (with status)
- Experiment Lifecycle
- Rules (messy OK, document learnings, promote only proven)

---

**Current State:** Ready to fork. All files prepared. Just need to execute steps.
**Risk of Compacting:** ✅ LOW - All key decisions documented here
**Next Session:** Start fresh, read this handoff, execute fork

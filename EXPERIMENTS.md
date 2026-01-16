# Chess Analysis Experiments

⚠️ **This is the experimental/development repository.**

👉 **For production code, see: [chessdotcomcoach](https://github.com/vds4321/chessdotcomcoach)**

---

## What This Repo Is

Fast-moving experimentation with:
- LLM-enhanced coaching
- Multi-model comparisons (Claude, GPT-4, Llama)
- Advanced ML features
- New analysis techniques

Code here is **messy and volatile**. Features proven valuable get refactored and promoted to production.

---

## Active Experiments

### 🔬 LLM-Enhanced Coaching (Planned)
**Status:** Not started
**Branch:** `llm-coaching-poc`
**Goal:** Use Claude/GPT to generate coaching insights from tactical analysis
**Success Criteria:**
- Provides actionable chess advice better than just reading stats
- Code <150 lines, obvious behavior
- Actually helps improve chess (not generic advice)

**Approach:**
- Start with single skill: tactical mistake explanation
- No abstraction layer (prove value first)
- Document in LEARNINGS.md

### 📊 Multi-Model Comparison (Planned)
**Status:** Not started
**Branch:** TBD
**Goal:** Compare Claude vs GPT-4 vs Llama for chess advice quality
**Success Criteria:**
- Identify which models best for different chess tasks
- Performance metrics (latency, cost, quality)
- Recommendation engine for model selection

### ✅ Opening Recommender System (Completed)
**Status:** ✅ Promoted to production
**Result:** Collaborative filtering works well for opening recommendations
**Location:** Production repo - `src/analyzers/opening_recommender.py`
**Learning:** ML-based recommendations outperform simple statistics for repertoire building

---

## Experiment Lifecycle

```
1. EXPERIMENT (here)
   ├─ Try ideas, break things, iterate fast
   ├─ AI-assisted rapid prototyping
   └─ Document in LEARNINGS.md

2. VALIDATE
   ├─ Does it actually help chess?
   ├─ Is code clean and understandable?
   └─ Can it be tested?

3. REFACTOR
   ├─ Simplify, remove bloat
   ├─ Write proper tests
   └─ Document clearly

4. PROMOTE
   ├─ Cherry-pick clean commits to production
   └─ Update production README

5. ARCHIVE
   ├─ Document learning (even if failed)
   └─ Delete experimental code (keep in git history)
```

---

## Rules for This Repo

### ✅ Allowed
- Messy code (that's the point of experiments)
- Breaking changes
- Trying crazy ideas
- AI-generated boilerplate (review before committing)
- Multiple approaches to same problem
- Failed experiments (if documented)

### ❌ Not Allowed
- Promoting untested code to production
- Experimenting directly on main branch (use feature branches)
- Skipping documentation in LEARNINGS.md
- Keeping dead code around (archive or delete)

---

## Current Focus

**Next Experiment:** LLM-Enhanced Coaching POC

**Timeline:**
- Week 1: Single skill proof of concept (`chess_coach.py`)
- Week 2: Validate with real games, iterate
- Week 3: If successful, refactor and promote to production

**Tracking:** See `LEARNINGS.md` for daily progress

---

## Using This Repo

**If you want to USE chess analysis:**
→ Go to [chessdotcomcoach](https://github.com/vds4321/chessdotcomcoach) (production)

**If you want to EXPERIMENT with cutting-edge features:**
→ You're in the right place

**If you want to CONTRIBUTE:**
→ Start with production repo for bug fixes/improvements
→ Use this repo to propose new features (create experiment branch)

---

## Experiment → Production Flow

```bash
# 1. Create experiment branch
git checkout -b llm-coaching-poc

# 2. Iterate fast (AI-assisted, break things, try ideas)
# ... rapid development ...

# 3. Document learnings
echo "## LLM Coaching POC - Day 3" >> LEARNINGS.md
echo "Finding: Claude 3.5 better than GPT-4 for chess" >> LEARNINGS.md

# 4. When something works
git add src/llm/chess_coach.py tests/test_chess_coach.py
git commit -m "Working: LLM tactical coaching"

# 5. Cherry-pick to production (after cleanup)
cd ../chessdotcomcoach
git cherry-pick abc123  # Clean, tested feature only

# 6. Delete experimental mess (keep learnings)
cd ../chessAnalysit
git checkout main
git branch -D llm-coaching-poc
# (code preserved in git history + LEARNINGS.md)
```

---

## Experiment History

### Completed
- ✅ **Opening Recommender** (2024-01) - Promoted to production
- ✅ **ML-based Similarity** (2024-01) - Collaborative filtering works

### In Progress
- 🔬 **LLM Coaching** (2024-01) - Proof of concept phase

### Archived (Failed)
- ❌ None yet

---

**Remember:** Experiments should be fast, messy, and educational. Production code should be clean, tested, and valuable.

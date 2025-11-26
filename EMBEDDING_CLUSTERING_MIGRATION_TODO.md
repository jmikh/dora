# Embedding & Clustering Scripts Migration TODO

## Summary

The embedding and clustering scripts need to be updated to work with the new database schema:
- ❌ OLD: `insights` table with `insight_type` field
- ✅ NEW: `complaints` table without `insight_type` field

## Current Status

### ✅ UPDATED Scripts

1. **`generate_embeddings.py`** - FULLY MIGRATED
   - ✅ Removed `insight_type` parameter
   - ✅ Uses `Complaint` model instead of `Insight`
   - ✅ Uses `Company` table for filtering
   - ✅ Joins through `reddit_content` and `reviews` tables
   - ✅ Generates embeddings for unique complaints
   - ✅ Saves to JSON file (not database)
   - ✅ Tested and working

**Usage:**
```bash
python generate_embeddings.py --company wispr --output embeddings_wispr.json
python generate_embeddings.py --company wispr --limit 10 --output test_embeddings.json
```

---

### ✅ UPDATED Scripts

2. **`generate_reduced_embeddings.py`** - FULLY MIGRATED
   - ✅ Removed `insight_type` parameter
   - ✅ Uses `ComplaintEmbedding` model instead of `Insight`
   - ✅ Reads from complaint_embeddings table (1536D)
   - ✅ Saves to complaint_embeddings table with target dimensions
   - ✅ Filters by company using joins through reddit_content and reviews
   - ✅ Uses UMAP for dimensionality reduction
   - ✅ Tested and working

**Usage:**
```bash
python generate_reduced_embeddings.py --company wispr --dimensions 50
python generate_reduced_embeddings.py --company wispr --dimensions 20
python generate_reduced_embeddings.py --company wispr --dimensions 50 --force  # Regenerate
```

---

3. **`cluster_insights.py`** - FULLY MIGRATED
   - ✅ Removed `insight_type` parameter
   - ✅ Uses `ComplaintEmbedding` model instead of `Insight`
   - ✅ Reads from complaint_embeddings table
   - ✅ Filters by company using joins through reddit_content and reviews
   - ✅ Uses HDBSCAN for clustering
   - ✅ Saves clusters to database with insight_type=NULL
   - ✅ Migrated clusters table to make insight_type nullable
   - ✅ Tested and working

**Usage:**
```bash
python cluster_insights.py --company wispr --dimensions 50 --min-cluster-size 5
python cluster_insights.py --company wispr --dimensions 20 --min-cluster-size 3
```

**Results:**
- Successfully clustered 612 complaints into 38 clusters
- 115 noise points (unclustered)
- Average cluster size: 13 complaints
- Cluster size range: 5-37 complaints

---

4. **`hierarchical_clustering.py`** - NEEDS MIGRATION
   - Uses old `Insight` model
   - References `insight_type` field
   - Creates hierarchical clusters

**Required changes:**
- [ ] Same as cluster_insights.py
- [ ] Update cluster hierarchy logic

---

5. **`label_clusters.py`** - MIGHT BE OK
   - Works with `clusters` table
   - Uses LLM to generate labels
   - May work as-is if clusters table is compatible

**Need to check:**
- [ ] Verify it doesn't rely on `insight_type`
- [ ] Test with new complaints-based clusters

---

## Architecture Decisions Needed

### Decision 1: Where to Store Embeddings?

**Option A: JSON Files (Current approach)**
```
embeddings_wispr.json - Full embeddings
embeddings_wispr_reduced_5d.json - 5D reduced embeddings
```
✅ Pros: Easy to version control, portable
❌ Cons: Need to keep in sync with database

**Option B: Database Table**
```sql
CREATE TABLE complaint_embeddings (
    complaint TEXT PRIMARY KEY,
    embedding TEXT,  -- JSON
    reduced_embedding_5 TEXT,  -- JSON
    reduced_embedding_10 TEXT  -- JSON
);
```
✅ Pros: Single source of truth
❌ Cons: Larger database, harder to version

**Recommendation:** Start with JSON files (Option A), easier to iterate

---

### Decision 2: How to Associate Complaints with Clusters?

**Option A: Update clusters table schema**
```sql
-- Keep existing clusters table structure but remove insight_type
clusters (
    id INTEGER PRIMARY KEY,
    company_name TEXT,
    embedding_type TEXT,  -- 'original' or 'reduced'
    n_components INTEGER,
    cluster_label TEXT,
    cluster_summary TEXT,
    size INTEGER,
    created_at DATETIME
)

-- Add new junction table
CREATE TABLE complaint_cluster_assignments (
    id INTEGER PRIMARY KEY,
    complaint TEXT,
    cluster_id INTEGER,
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);
```

**Option B: Store cluster assignments in JSON**
```json
{
  "cluster_0": ["Cannot disable AI formatting", "Forced AI editing"],
  "cluster_1": ["Poor Bluetooth support", "AirPods not working"]
}
```

**Recommendation:** Option A (database table) for queryability

---

## Migration Plan

### Phase 1: Core Embedding Generation ✅ DONE
- [x] Update generate_embeddings.py
- [x] Test with complaints table
- [x] Save to complaint_embeddings table with dimensions=1536
- [x] Generated 612 embeddings for wispr

### Phase 2: Dimensionality Reduction ✅ DONE
- [x] Update generate_reduced_embeddings.py
- [x] Read from complaint_embeddings table (dimensions=1536)
- [x] Save reduced embeddings to complaint_embeddings table
- [x] Test with UMAP on 612 complaints
- [x] Generated 50D and 20D embeddings successfully

### Phase 3: Clustering ✅ DONE
- [x] Update cluster_insights.py
- [x] Read from complaint_embeddings table
- [x] Create clusters in database
- [x] Migrate clusters table to make insight_type nullable
- [x] Test HDBSCAN clustering
- [x] Successfully clustered 612 complaints into 38 clusters

### Phase 4: Cluster Labeling
- [ ] Update label_clusters.py if needed
- [ ] Test LLM labeling on complaint clusters

### Phase 5: Testing & Validation
- [ ] Run full pipeline on Wispr complaints
- [ ] Verify cluster quality
- [ ] Compare with old insights-based clusters

---

## Quick Start: Running Current Working Scripts

```bash
# 1. Generate 1536D embeddings for complaints
python generate_embeddings.py --company wispr
# Output: Saves to complaint_embeddings table with dimensions=1536
# Result: 612 complaint embeddings created

# 2. Generate reduced embeddings (50D)
python generate_reduced_embeddings.py --company wispr --dimensions 50
# Output: Saves to complaint_embeddings table with dimensions=50
# Result: 612 reduced embeddings created

# 3. Generate reduced embeddings (20D)
python generate_reduced_embeddings.py --company wispr --dimensions 20
# Output: Saves to complaint_embeddings table with dimensions=20
# Result: 612 reduced embeddings created

# 4. Cluster complaints using HDBSCAN
python cluster_insights.py --company wispr --dimensions 50 --min-cluster-size 5
# Output: Saves clusters to database
# Result: 38 clusters created (497 clustered, 115 noise)

# 5. Check database
sqlite3 dora.db "SELECT dimensions, COUNT(*) FROM complaint_embeddings GROUP BY dimensions"
# Output:
# 20|612
# 50|612
# 1536|612

sqlite3 dora.db "SELECT COUNT(*), AVG(size) FROM clusters WHERE company_name='wispr'"
# Output:
# 38|13.08

# 6. NEXT: Update label_clusters.py to generate cluster labels
```

---

## Notes

- The old `insights` table has been dropped, so old scripts will fail
- All scripts should now use the `complaints` table
- Complaints don't have an `insight_type` - they're just complaints
- We have 612 unique complaints across Reddit + Reviews
- Each complaint has a `quote` field with the exact source text
- Complaints are linked to source content via `source_id` + `source_table`

---

## Questions to Answer

1. **Do we need reduced embeddings?**
   - UMAP reduces 1536D → 5D or 10D for clustering
   - Could cluster directly on full embeddings (slower but works)

2. **What clustering algorithm?**
   - HDBSCAN: Good for varying density clusters
   - K-means: Faster but requires setting k
   - Agglomerative: Good for hierarchical clusters

3. **How to evaluate clusters?**
   - Silhouette score
   - Manual inspection
   - LLM-based quality assessment

4. **Do we want to cluster across sources or separately?**
   - Combined: All complaints together
   - Separate: Reddit complaints vs Review complaints
   - Recommendation: Start combined, can separate later

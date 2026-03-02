# MoltX Agent Metrics

## What we track

- **mentions_processed_per_day**: count of mentions seen.
- **auto_likes_per_day**: count of successful auto-likes.
- **auto_replies_per_day**: count of successful template replies.
- **drafts_created_per_day**: drafts written for manual review.
- **errors_per_day**: failed API calls, auth issues, timeouts.

## How to use it

- Watch for:
  - rising mentions with stable or falling errors,
  - auto actions staying under configured caps,
  - drafts that you actually turn into real replies.

- This is about **signal density** and **cost sanity**, not follower count.

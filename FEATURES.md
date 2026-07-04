# Kisii TV — Features Summary

This document lists the current features of the Kisii TV website for client review and demonstration.

## Quick Overview
- Type: Django-based streaming site (Django 5.x)
- Content storage: SQLite (local) / configurable for Postgres on deploy
- Deployment: Docker-ready, Render-ready; demo available via ngrok

## Public-facing Features
- **Homepage / Broadcast Experience**: Cinematic hero with featured player, live banner, featured content rail, and breaking ticker.
- **Featured Player**: Embedded video player (YouTube/Vimeo) with fallback and playlist context.
- **Live Now Banner**: Prominent live badge + live stream link when a `Video` is flagged `is_live`.
- **Schedule Ticker & Panel**: Program schedule pulled from `ScheduleEntry` records and rendered in a scrolling ticker/panel.
- **Trending & Featured Carousels**: Now Trending rail and featured content carousels with thumbnail, title, meta.
- **Playlist Rail**: Horizontally scrollable featured videos rail with preview card.

## Content & Discovery
- **Categories**: Videos organized by `Category`; category pages list content by date.
- **Search**: Full-text search across title, description, category and filtering by category and sort options (recent, popular, likes).
- **Related Content**: Video detail pages show related videos from the same category.

## User Engagement
- **Comments**: Visitors can submit comments; admin can approve/disapprove via Django admin.
- **Likes**: Authenticated users can like/unlike videos; like counts are stored and displayed.
- **Watchlist**: Authenticated users can add/remove videos to a personal watchlist.
- **Continue Watching**: Session-based watch history and an authenticated fallback that surfaces recently liked videos.
- **Newsletter**: Simple subscribe endpoint that stores subscribers in `NewsletterSubscriber`.

## Personalization & Recommendations
- **For You**: Personalized suggestions combining recently watched items and liked categories.
- **Trending Score**: `Video.trending_score` ranks trending content by views and recency.
- **Most Liked / Recommended**: Dedicated sections for high-engagement and recommended videos.

## Admin & Content Management
- **Django Admin**: Full management for `Category`, `Video`, `Comment`, `NewsletterSubscriber`, `WatchlistItem`, `VideoLike`, `ScheduleEntry`.
- **Schedule Management**: Create and reorder broadcast schedule entries from the admin UI.
- **Demo Admin**: `demo_admin` (local DB) was created for review — remove/change before production.

## Developer / Deployment Notes
- **Repository**: https://github.com/davidotieno13827-cell/kisiitv.co.ke.git (branch: `main`)
- **Containerization**: `Dockerfile` included; uses `gunicorn` to serve the app.
- **Render**: `render.yaml` is provided for easy Render deployment.
- **Local Demo**: ngrok tunnel available for quick sharing during review.

## Demo Access (during review)
- Demo URL: (share the active ngrok or staging URL)
- Admin: `demo_admin` / `DemoPass123!` (local demo database) — rotate before production.

## Recommended Next Steps (optional)
- Move media and static files to S3 or a CDN for production.
- Configure persistent Postgres DB for staging/production.
- Add unit/integration tests for schedule and recommendation logic (some tests already exist).
- Add GitHub Actions or Render Auto-deploy with PR previews for professional review flow.

---
If you want, I can tailor this into a styled one-page PDF or add screenshots and direct links (admin, live URL) for the client presentation.

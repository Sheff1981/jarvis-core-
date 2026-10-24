# JARVIS Social Studio — design specification

## Purpose
Personal social-media production and management module. Integrates into existing JARVIS core, not a separate assistant.

## Platforms
- VK: community setup, branding, posts, scheduling, moderation, analytics, commerce when supported by official VK APIs.
- Instagram: professional-account content planning, permitted publishing and insights through Meta Graph API with required account permissions. Account/profile creation is not promised as API functionality.
- Telegram: channels, post scheduling and moderation through Bot API where the bot has suitable admin rights. Creating channels may require manual action in Telegram.
- Web pages: generate landing pages and media assets with user review.

## Workflow
1. User specifies brand, platform, audience, objectives, and tone; infer only non-sensitive reusable preferences from explicit project memory.
2. Draft editable content calendar, descriptions, visuals and post variants.
3. Present a preview and validation checklist; do not claim images exist until an image generator returns assets.
4. Request explicit, narrowly scoped approval for each account connection, community change, upload, publication, deletion, and paid promotion. Show account, destination, content, and timing.
5. Execute through official API with OAuth/scoped credentials; log external action identifiers and result.
6. Support rollback or correction where API permits; never promise reversible publication.

## Security and privacy
- No account password collection in chat or in prompts.
- OAuth tokens stored in OS-protected credential store, never in SQLite conversation memory, logs, or generated content.
- Default draft-only mode; no unattended posting without separately configured permissions.
- Per-account isolation; no cross-posting by default.
- Do not mass-message, scrape private data, inflate engagement, evade rate limits or platform protections.
- Respect intellectual property and obtain rights to assets.

## Architecture
SocialStudio interface with adapters VK, Instagram, Telegram; ContentDraft, AssetReference, PublicationPlan, ApprovalRecord, PublicationReceipt. Each adapter exposes capabilities rather than assuming every platform supports every operation. Use existing permission gate for user intent; persist approval scope and receipts for external actions.

## Release milestones
S1: local draft storage, content calendar and preview, no external account access.
S2: authorized platform connections, read-only capability checks.
S3: reviewed single-post publishing with receipts and tests.
S4: opt-in scheduling, analytics, moderation and optional visual generation.
No claim of completed integration before real API tests.

from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import Post
from home.services.trading import (
    build_embed_payload_from_payload,
    create_real_estate_journal_from_embed,
    create_stock_journal_from_embed,
)


class Command(BaseCommand):
    """Normalize existing trading posts and back-fill journals/dashboard data."""

    help = "Normalize trading embed payloads and create missing journal/portfolio records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview the number of posts that would be updated without making changes.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        queryset = Post.objects.select_related("user").order_by("id")

        processed = 0
        normalized_updates = 0
        stock_created = 0
        real_estate_created = 0

        for post in queryset:
            embed_payload = post.embed_payload_json or {}
            asset_type = (embed_payload.get("asset_type") or "").lower()

            normalized_payload = embed_payload
            if asset_type not in {"stock", "real_estate"}:
                normalized_payload = build_embed_payload_from_payload(embed_payload)

            if not normalized_payload:
                continue

            processed += 1

            embed_changed = normalized_payload is not embed_payload or normalized_payload != embed_payload

            if dry_run:
                if embed_changed:
                    normalized_updates += 1
                if normalized_payload.get("asset_type") == "stock" and not post.stock_trade_id:
                    stock_created += 1
                elif normalized_payload.get("asset_type") == "real_estate" and not post.re_deal_id:
                    real_estate_created += 1
                continue

            with transaction.atomic():
                if embed_changed:
                    post.embed_payload_json = normalized_payload
                    post.save(update_fields=["embed_payload_json"])
                    normalized_updates += 1

                asset_type = normalized_payload.get("asset_type")
                if asset_type == "stock" and not post.stock_trade_id:
                    create_stock_journal_from_embed(post.user, post, normalized_payload)
                    stock_created += 1
                elif asset_type == "real_estate" and not post.re_deal_id:
                    create_real_estate_journal_from_embed(post.user, post, normalized_payload)
                    real_estate_created += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run mode: no changes were applied."))
        self.stdout.write(f"Posts examined: {processed}")
        self.stdout.write(f"Embed payloads normalized: {normalized_updates}")
        self.stdout.write(f"Stock journals created: {stock_created}")
        self.stdout.write(f"Real estate journals created: {real_estate_created}")

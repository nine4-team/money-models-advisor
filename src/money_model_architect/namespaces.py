"""Namespace taxonomy for the local proof harness.

The hosted architecture plans Pinecone namespaces. This local module keeps the
same modeling decision executable without requiring external credentials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterRoute:
    chapter: str
    primary_layer: str
    secondary_layers: tuple[str, ...] = ()

    @property
    def layers(self) -> tuple[str, ...]:
        return (self.primary_layer, *self.secondary_layers)


CHAPTER_ROUTES: dict[str, ChapterRoute] = {
    "cac": ChapterRoute("cac", "unit-economics", ("offers",)),
    "payback-period": ChapterRoute("payback-period", "unit-economics", ("upsells", "continuity")),
    "gross-profit": ChapterRoute("gross-profit", "unit-economics"),
    "cfa": ChapterRoute("cfa", "unit-economics"),
    "how-businesses-make-money": ChapterRoute("how-businesses-make-money", "unit-economics"),
    "context": ChapterRoute("context", "unit-economics"),
    "attraction-offers": ChapterRoute("attraction-offers", "offers"),
    "offer-types": ChapterRoute("offer-types", "offers", ("upsells", "downsells", "continuity")),
    "decoy-offers": ChapterRoute("decoy-offers", "offers"),
    "free-giveaways": ChapterRoute("free-giveaways", "offers"),
    "free-trials": ChapterRoute("free-trials", "downsells", ("offers",)),
    "free-with-consumption": ChapterRoute("free-with-consumption", "offers"),
    "upsell-offers": ChapterRoute("upsell-offers", "upsells"),
    "classic-upsell": ChapterRoute("classic-upsell", "upsells"),
    "menu-upsell": ChapterRoute("menu-upsell", "upsells"),
    "anchor-upsell": ChapterRoute("anchor-upsell", "upsells"),
    "rollover-upsell": ChapterRoute("rollover-upsell", "upsells"),
    "buy-x-get-y": ChapterRoute("buy-x-get-y", "offers", ("upsells", "continuity")),
    "downsells": ChapterRoute("downsells", "downsells"),
    "feature-downsells": ChapterRoute("feature-downsells", "downsells"),
    "pay-less-now": ChapterRoute("pay-less-now", "offers", ("downsells",)),
    "payment-plans": ChapterRoute("payment-plans", "downsells"),
    "waived-fee": ChapterRoute("waived-fee", "continuity"),
    "win-your-money-back": ChapterRoute("win-your-money-back", "offers"),
    "continuity-offers": ChapterRoute("continuity-offers", "continuity"),
    "continuity-bonus": ChapterRoute("continuity-bonus", "continuity"),
    "continuity-discounts": ChapterRoute("continuity-discounts", "continuity"),
    "make-your-money-model": ChapterRoute("make-your-money-model", "offers", ("unit-economics", "upsells", "downsells", "continuity")),
    "money-models-offer-stacks": ChapterRoute("money-models-offer-stacks", "offers", ("unit-economics", "upsells", "downsells", "continuity")),
    "ten-years-ten-minutes": ChapterRoute("ten-years-ten-minutes", "unit-economics", ("offers", "upsells", "downsells", "continuity")),
    "ride-along-apprenticeship": ChapterRoute("ride-along-apprenticeship", "offers", ("unit-economics", "upsells", "downsells", "continuity")),
    "final-words": ChapterRoute("final-words", "unit-economics", ("offers", "upsells", "downsells", "continuity")),
}

LAYERS = ("unit-economics", "offers", "upsells", "downsells", "continuity")


def route_for_chapter(chapter: str) -> ChapterRoute:
    return CHAPTER_ROUTES.get(chapter, ChapterRoute(chapter, "offers"))


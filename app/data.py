"""
Task datasets for the review-sentiment-env environment.

Each review entry contains:
  - review: the raw customer review text
  - sentiment: ground truth sentiment (positive / negative / neutral)
  - decision: ground truth moderation label (allow / flag)
"""

EASY_TASK = [
    {
        "review": "I love this product, it's absolutely amazing! Best purchase ever.",
        "sentiment": "positive",
        "decision": "allow",
    },
    {
        "review": "This is the worst thing I have ever bought. Complete garbage.",
        "sentiment": "negative",
        "decision": "allow",
    },
    {
        "review": "Fantastic quality! I will definitely buy again. Highly recommend.",
        "sentiment": "positive",
        "decision": "allow",
    },
    {
        "review": "Totally broken on arrival. Waste of money. Never buying again.",
        "sentiment": "negative",
        "decision": "allow",
    },
    {
        "review": "Buy cheap replicas of this at www.fakeshop.biz — way better price!",
        "sentiment": "positive",
        "decision": "flag",
    },
]

MEDIUM_TASK = [
    {
        "review": "Good product overall but the delivery was really slow.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "It's okay, not great but not terrible either. Does the job.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "Quality seems decent but the packaging was damaged when it arrived.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "Works fine I guess. I've seen better, but also much worse.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "Great product! Find exact same item for 50% off at cheap-stuff-deals.ru",
        "sentiment": "positive",
        "decision": "flag",
    },
    {
        "review": "I hate people who sell this. The seller is a total SCAMMER!! AVOID!!!",
        "sentiment": "negative",
        "decision": "flag",
    },
]

HARD_TASK = [
    {
        "review": "Wow, amazing service... only waited 3 hours for support 🙃 totally worth it.",
        "sentiment": "negative",
        "decision": "allow",
    },
    {
        "review": "Better than expected, but wow is it overpriced for what you get.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "Oh sure, because who doesn't love when a product breaks on day one. Brilliant.",
        "sentiment": "negative",
        "decision": "allow",
    },
    {
        "review": "Five stars! I received a free unit for this review. Totally unbiased opinion.",
        "sentiment": "positive",
        "decision": "flag",
    },
    {
        "review": "Not bad. Not good. It exists and it technically functions. That's about it.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "I mean... if you enjoy disappointment, this is the product for you!",
        "sentiment": "negative",
        "decision": "allow",
    },
    {
        "review": "This item is great! DM me @promo_deals_99 on Telegram for a discount code.",
        "sentiment": "positive",
        "decision": "flag",
    },
    {
        "review": "Surprisingly good. I expected nothing and it still almost met my expectations.",
        "sentiment": "neutral",
        "decision": "allow",
    },
    {
        "review": "The features are great on paper. It’s just a shame they don’t seem to exist in reality.",
        "sentiment": "negative",
        "decision": "allow",
    }
    ,
    {
        "review": "This app has completely changed my routine — now I spend more time fixing issues than actually using it.",
        "sentiment": "negative",
        "decision": "allow",
    }
]

TASKS = {
    "easy": EASY_TASK,
    "medium": MEDIUM_TASK,
    "hard": HARD_TASK,
}

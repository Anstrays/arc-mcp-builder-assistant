#!/usr/bin/env python3
"""Dependency-free secret scan for the repository.

Scans tracked and untracked text files for common credential patterns:
- GitHub personal access tokens
- AWS access keys
- Slack / Telegram bot tokens
- Generic API keys, secrets, passwords, private keys
- PEM/OpenSSH/EC private keys
- Ethereum-style 64-hex private keys
- Committed .env files or shell history
- 12/24-word BIP-39 mnemonic seed phrases

Exit codes:
    0 - no obvious secrets found
    1 - potential secret pattern detected (prints paths and pattern names)

This script intentionally contains regex patterns; it skips itself and other
secret-scanning code when scanning.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Extensions and suffixes that may contain text secrets.
TEXT_SUFFIXES = {
    "",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

# Paths that legitimately describe credential patterns or scan for them.
SKIP_PATHS = {
    ROOT / "scripts/scan_for_secrets.py",
    ROOT / "scripts/validate_repo.py",
    ROOT / ".git",
    ROOT / "__pycache__",
}

# BIP-39 English wordlist subset used to flag multi-word seed phrases.
# Keeping the list short but distinctive reduces false positives while still
# catching obvious pasted mnemonics.
BIP39_WORDS = {
    "abandon", "ability", "able", "about", "above", "absent", "absorb",
    "abstract", "absurd", "abuse", "access", "accident", "account",
    "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict",
    "address", "adjust", "admit", "adult", "advance", "advice", "aerobic",
    "affair", "afford", "afraid", "again", "age", "agent", "agree",
    "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol",
    "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha",
    "already", "also", "alter", "always", "amateur", "amazing", "among",
    "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle",
    "angry", "animal", "ankle", "announce", "annual", "another", "answer",
    "antenna", "antique", "anxiety", "any", "apart", "apology", "appear",
    "apple", "approve", "april", "arch", "arctic", "area", "arena", "argue",
    "arm", "armed", "armor", "army", "around", "arrange", "arrest",
    "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask",
    "aspect", "assault", "asset", "assist", "assume", "asthma", "athlete",
    "atom", "attack", "attend", "attitude", "attract", "auction", "audit",
    "august", "aunt", "author", "auto", "autumn", "average", "avocado",
    "avoid", "awake", "aware", "away", "awesome", "awful", "awkward", "axis",
    "baby", "bachelor", "bacon", "badge", "bag", "balance", "balcony",
    "ball", "bamboo", "banana", "banner", "bar", "barely", "bargain",
    "barrel", "base", "basic", "basket", "battle", "beach", "bean", "beauty",
    "because", "become", "beef", "before", "begin", "behave", "behind",
    "believe", "below", "belt", "bench", "benefit", "best", "betray",
    "better", "between", "beyond", "bicycle", "bid", "bike", "bind",
    "biology", "bird", "birth", "bitter", "black", "blade", "blame",
    "blanket", "blast", "bleak", "bless", "blind", "blood", "blossom",
    "blouse", "blue", "blur", "blush", "board", "boat", "body", "boil",
    "bomb", "bone", "bonus", "book", "boost", "border", "boring", "borrow",
    "boss", "bottom", "bounce", "box", "boy", "bracket", "brain", "brand",
    "brass", "brave", "bread", "breeze", "brick", "bridge", "brief",
    "bright", "brilliant", "bring", "brisk", "broccoli", "broken", "bronze",
    "broom", "brother", "brown", "brush", "bubble", "buddy", "budget",
    "buffalo", "build", "bulb", "bulk", "bullet", "bundle", "bunker",
    "burden", "burger", "burst", "bus", "business", "busy", "butter",
    "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage",
    "cake", "call", "calm", "camera", "camp", "can", "canal", "cancel",
    "candy", "cannon", "canoe", "canvas", "canyon", "capable", "capital",
    "captain", "car", "carbon", "card", "cargo", "carpet", "carry", "cart",
    "case", "cash", "casino", "castle", "casual", "cat", "catalog", "catch",
    "category", "cattle", "caught", "cause", "caution", "cave", "ceiling",
    "celery", "cement", "census", "century", "cereal", "certain", "chair",
    "chalk", "champion", "change", "chaos", "chapter", "charge", "chase",
    "chat", "cheap", "check", "cheese", "chef", "cherry", "chest", "chicken",
    "chief", "child", "chimney", "choice", "choose", "chronic", "chuckle",
    "chunk", "churn", "cigar", "cinnamon", "circle", "citizen", "city",
    "civil", "claim", "clap", "clarify", "claw", "clay", "clean", "clerk",
    "clever", "click", "client", "cliff", "climb", "clinic", "clip", "clock",
    "clog", "close", "cloth", "cloud", "clown", "club", "clump", "cluster",
    "clutch", "coach", "coast", "coconut", "code", "coffee", "coil", "coin",
    "collect", "color", "column", "combine", "come", "comfort", "comic",
    "common", "company", "concert", "conduct", "confirm", "congress",
    "connect", "consider", "control", "convince", "cook", "cool", "copper",
    "copy", "coral", "core", "corn", "correct", "cost", "cotton", "couch",
    "country", "couple", "courage", "course", "cousin", "cover", "coyote",
    "crack", "cradle", "craft", "cram", "crane", "crash", "crater", "crawl",
    "crazy", "cream", "credit", "creek", "crew", "cricket", "crime", "crisp",
    "critic", "crop", "cross", "crouch", "crowd", "crucial", "cruel",
    "cruise", "crumble", "crunch", "crush", "cry", "crystal", "cube",
    "culture", "cup", "cupboard", "curious", "current", "curtain", "curve",
    "cushion", "custom", "cute", "cycle", "dad", "damage", "damp", "dance",
    "danger", "daring", "dash", "daughter", "dawn", "day", "deal", "debate",
    "debris", "decade", "december", "decide", "decline", "decorate",
    "decrease", "deer", "defense", "define", "defy", "degree", "delay",
    "deliver", "demand", "demise", "denial", "dentist", "deny", "depart",
    "depend", "deposit", "depth", "deputy", "derive", "describe", "desert",
    "design", "desk", "despair", "destroy", "detail", "detect", "develop",
    "device", "devote", "diagram", "dial", "diamond", "diary", "dice",
    "diesel", "diet", "differ", "digital", "dignity", "dilemma", "dinner",
    "dinosaur", "direct", "dirt", "disagree", "discover", "disease", "dish",
    "dismiss", "disorder", "display", "distance", "divert", "divide",
    "divorce", "dizzy", "doctor", "document", "dog", "doll", "dolphin",
    "domain", "donate", "donkey", "donor", "door", "dose", "double", "dove",
    "draft", "dragon", "drama", "drastic", "draw", "dream", "dress", "drift",
    "drill", "drink", "drip", "drive", "drop", "drum", "dry", "duck", "dumb",
    "dune", "during", "dust", "dutch", "duty", "dwarf", "dynamic", "eager",
    "eagle", "early", "earn", "earth", "easily", "east", "easy", "echo",
    "ecology", "economy", "edge", "edit", "educate", "effort", "egg",
    "eight", "either", "elbow", "elder", "electric", "elegant", "element",
    "elephant", "elevator", "elite", "else", "embark", "embody", "embrace",
    "emerge", "emotion", "employ", "empower", "empty", "enable", "enact",
    "end", "endless", "endorse", "enemy", "energy", "enforce", "engage",
    "engine", "enhance", "enjoy", "enlist", "enough", "enrich", "enroll",
    "ensure", "enter", "entire", "entry", "envelope", "episode", "equal",
    "equip", "era", "erase", "erode", "erosion", "error", "erupt", "escape",
    "essay", "essence", "estate", "eternal", "ethics", "evidence", "evil",
    "evoke", "evolve", "exact", "example", "excess", "exchange", "excite",
    "exclude", "excuse", "execute", "exercise", "exhaust", "exhibit", "exile",
    "exist", "exit", "exotic", "expand", "expect", "expire", "explain",
    "expose", "express", "extend", "extra", "eye", "eyebrow", "fabric",
    "face", "faculty", "fade", "faint", "faith", "fall", "false", "fame",
    "family", "famous", "fan", "fancy", "fantasy", "farm", "fashion", "fat",
    "fatal", "father", "fatigue", "fault", "favorite", "feature", "february",
    "federal", "fee", "feed", "feel", "female", "fence", "festival", "fetch",
    "fever", "few", "fiber", "fiction", "field", "figure", "file", "film",
    "filter", "final", "find", "fine", "finger", "finish", "fire", "firm",
    "first", "fiscal", "fish", "fit", "fitness", "fix", "flag", "flame",
    "flash", "flat", "flavor", "flee", "flight", "flip", "float", "flock",
    "floor", "flower", "fluid", "flush", "fly", "foam", "focus", "fog",
    "foil", "fold", "follow", "food", "foot", "force", "forest", "forget",
    "fork", "fortune", "forum", "forward", "fossil", "foster", "found",
    "fox", "fragile", "frame", "frequent", "fresh", "friend", "fringe",
    "frog", "from", "front", "frost", "frown", "frozen", "fruit", "fuel",
    "fun", "funny", "furnace", "fury", "future", "gadget", "gain", "galaxy",
    "gallery", "game", "gap", "garage", "garbage", "garden", "garlic",
    "garment", "gas", "gasp", "gate", "gather", "gauge", "gaze", "general",
    "genius", "genre", "gentle", "genuine", "gesture", "ghost", "giant",
    "gift", "giggle", "ginger", "giraffe", "girl", "give", "glad", "glance",
    "glare", "glass", "glide", "glimpse", "globe", "gloom", "glory", "glove",
    "glow", "glue", "goat", "goddess", "gold", "good", "goose", "gorilla",
    "gospel", "gossip", "govern", "gown", "grab", "grace", "grain", "grant",
    "grape", "grass", "gravity", "great", "green", "grid", "grief", "grit",
    "grocery", "group", "grow", "grunt", "guard", "guess", "guide", "guilt",
    "guitar", "gun", "gym", "habit", "hair", "half", "hammer", "hamster",
    "hand", "happy", "harbor", "hard", "harsh", "harvest", "hat", "have",
    "hawk", "hazard", "head", "health", "heart", "heavy", "hedgehog",
    "height", "hello", "helmet", "help", "hen", "hero", "hidden", "high",
    "hill", "hint", "hip", "hire", "history", "hobby", "hockey", "hold",
    "hole", "holiday", "hollow", "holy", "home", "honey", "hood", "hope",
    "horn", "horror", "horse", "hospital", "host", "hotel", "hour", "hover",
    "hub", "huge", "human", "humble", "humor", "hundred", "hungry", "hunt",
    "hurdle", "hurry", "hurt", "husband", "hybrid", "ice", "icon", "idea",
    "identify", "idle", "ignore", "ill", "illegal", "illness", "image",
    "imitate", "immense", "immune", "impact", "impose", "improve", "impulse",
    "inch", "include", "income", "increase", "index", "indicate", "indoor",
    "industry", "infant", "inflict", "inform", "inhale", "inherit",
    "initial", "inject", "injury", "inmate", "inner", "innocent", "input",
    "inquiry", "insane", "insect", "inside", "inspire", "install", "intact",
    "interest", "into", "invest", "invite", "involve", "iron", "island",
    "isolate", "issue", "item", "ivory", "jacket", "jaguar", "jar", "jazz",
    "jealous", "jeans", "jelly", "jewel", "job", "join", "joke", "journey",
    "joy", "judge", "juice", "jump", "jungle", "junior", "junk", "just",
    "kangaroo", "keen", "keep", "ketchup", "key", "kick", "kid", "kidney",
    "kind", "kingdom", "kiss", "kit", "kitchen", "kite", "kitten", "kiwi",
    "knee", "knife", "knock", "know", "lab", "label", "labor", "ladder",
    "lady", "lake", "lamp", "language", "laptop", "large", "later", "latin",
    "laugh", "laundry", "lava", "law", "lawn", "lawsuit", "layer", "lazy",
    "leader", "leaf", "learn", "leave", "lecture", "left", "leg", "legal",
    "legend", "leisure", "lemon", "lend", "length", "lens", "leopard",
    "lesson", "letter", "level", "liar", "library", "license", "life",
    "lift", "light", "like", "limb", "limit", "link", "lion", "liquid",
    "list", "little", "live", "lizard", "load", "loan", "lobster", "local",
    "lock", "locust", "lodge", "log", "lonely", "long", "loop", "lottery",
    "loud", "lounge", "love", "loyal", "lucky", "luggage", "lumber", "lunar",
    "lunch", "luxury", "lyrics", "machine", "mad", "magic", "magnet", "maid",
    "mail", "main", "major", "make", "mammal", "man", "manage", "mango",
    "mansion", "manual", "maple", "marble", "march", "margin", "marine",
    "market", "marriage", "mask", "mass", "master", "match", "material",
    "math", "matrix", "matter", "maximum", "maze", "meadow", "mean", "measure",
    "meat", "mechanic", "medal", "media", "melody", "melt", "member",
    "memory", "men", "mental", "mention", "menu", "mercy", "merge", "merit",
    "merry", "mesh", "message", "metal", "method", "middle", "midnight",
    "milk", "million", "mimic", "mind", "minimum", "minor", "minute",
    "miracle", "mirror", "misery", "miss", "mistake", "mix", "mixed",
    "mixture", "mobile", "model", "modify", "mom", "moment", "monitor",
    "monkey", "monster", "month", "moon", "moral", "more", "morning",
    "mosquito", "mother", "motion", "motor", "mountain", "mouse", "move",
    "movie", "much", "muffin", "mule", "multiply", "muscle", "museum",
    "mushroom", "music", "must", "mutual", "myself", "mystery", "myth",
    "naive", "name", "napkin", "narrow", "nasty", "nation", "nature",
    "near", "neck", "need", "negative", "neglect", "neither", "nephew",
    "nerve", "nest", "net", "network", "neutral", "never", "news", "next",
    "nice", "night", "noble", "noise", "nominee", "noodle", "normal",
    "north", "nose", "notable", "note", "nothing", "notice", "novel", "now",
    "nuclear", "number", "nurse", "nut", "oak", "obey", "object", "oblige",
    "obscure", "observe", "obtain", "obvious", "occur", "ocean", "october",
    "odor", "off", "offer", "office", "often", "oil", "okay", "old", "olive",
    "olympic", "omit", "once", "one", "onion", "online", "only", "open",
    "opera", "opinion", "oppose", "option", "orange", "orbit", "orchard",
    "order", "ordinary", "organ", "orient", "original", "orphan", "ostrich",
    "other", "outdoor", "outer", "output", "outside", "oval", "oven", "over",
    "own", "owner", "oxygen", "oyster", "ozone", "pact", "paddle", "page",
    "pair", "palace", "palm", "panda", "panel", "panic", "panther", "paper",
    "parade", "parent", "park", "parrot", "party", "pass", "patch", "path",
    "patient", "patrol", "pattern", "pause", "pave", "payment", "peace",
    "peanut", "pear", "peasant", "pelican", "pen", "penalty", "pencil",
    "people", "pepper", "perfect", "permit", "person", "pet", "phone",
    "photo", "phrase", "physical", "piano", "picnic", "picture", "piece",
    "pig", "pigeon", "pill", "pilot", "pink", "pioneer", "pipe", "pistol",
    "pitch", "pizza", "place", "planet", "plastic", "plate", "play",
    "please", "pledge", "pluck", "plug", "plunge", "poem", "poet", "point",
    "polar", "pole", "police", "pond", "pony", "pool", "popular", "portion",
    "position", "possible", "post", "potato", "pottery", "poverty", "powder",
    "power", "practice", "praise", "predict", "prefer", "prepare", "present",
    "pretty", "prevent", "price", "pride", "primary", "print", "priority",
    "prison", "private", "prize", "problem", "process", "produce", "profit",
    "program", "project", "promote", "proof", "property", "prosper",
    "protect", "proud", "provide", "public", "pudding", "pull", "pulp",
    "pulse", "pumpkin", "punch", "pupil", "puppy", "purchase", "purity",
    "purpose", "purse", "push", "put", "puzzle", "pyramid", "quality",
    "quantum", "quarter", "question", "quick", "quit", "quiz", "quote",
    "rabbit", "raccoon", "race", "rack", "radar", "radio", "rail", "rain",
    "raise", "rally", "ramp", "ranch", "random", "range", "rapid", "rare",
    "rate", "rather", "raven", "raw", "razor", "ready", "real", "reason",
    "rebel", "rebuild", "recall", "receive", "recipe", "record", "recycle",
    "reduce", "reflect", "reform", "refuse", "region", "regret", "regular",
    "reject", "relax", "release", "relief", "rely", "remain", "remember",
    "remind", "remove", "render", "renew", "rent", "reopen", "repair",
    "repeat", "replace", "report", "require", "rescue", "resemble",
    "resist", "resource", "response", "result", "retire", "retreat",
    "return", "reunion", "reveal", "review", "reward", "rhythm", "rib",
    "ribbon", "rice", "rich", "ride", "ridge", "rifle", "right", "rigid",
    "ring", "riot", "ripple", "risk", "ritual", "rival", "river", "road",
    "roast", "robot", "robust", "rocket", "romance", "roof", "rookie",
    "room", "rose", "rotate", "rough", "round", "route", "royal", "rubber",
    "rude", "rug", "rule", "run", "runway", "rural", "sad", "saddle",
    "sadness", "safe", "sail", "salad", "salmon", "salon", "salt", "salute",
    "same", "sample", "sand", "satisfy", "satoshi", "sauce", "sausage",
    "save", "say", "scale", "scan", "scare", "scatter", "scene", "scheme",
    "school", "science", "scissors", "scorpion", "scout", "scrap", "screen",
    "script", "scrub", "sea", "search", "season", "seat", "second", "secret",
    "section", "security", "seed", "seek", "segment", "select", "sell",
    "seminar", "senior", "sense", "sentence", "series", "service",
    "session", "settle", "setup", "seven", "shadow", "shaft", "shallow",
    "share", "shed", "shell", "sheriff", "shield", "shift", "shine", "ship",
    "shiver", "shock", "shoe", "shoot", "shop", "short", "shoulder", "shove",
    "shrimp", "shrug", "shuffle", "shy", "sibling", "sick", "side", "siege",
    "sight", "sign", "silent", "silk", "silly", "silver", "similar",
    "simple", "since", "sing", "siren", "sister", "situate", "six", "size",
    "skate", "sketch", "ski", "skill", "skin", "skirt", "skull", "slab",
    "slam", "sleep", "slender", "slice", "slide", "slight", "slim", "slogan",
    "slot", "slow", "slush", "small", "smart", "smile", "smoke", "smooth",
    "snack", "snake", "snap", "sniff", "snow", "soap", "soccer", "social",
    "sock", "soda", "soft", "solar", "soldier", "solid", "solution", "solve",
    "someone", "song", "soon", "sorry", "sort", "soul", "sound", "soup",
    "source", "south", "space", "spare", "spatial", "spawn", "speak",
    "special", "speed", "spell", "spend", "sphere", "spice", "spider",
    "spike", "spin", "spirit", "split", "spoil", "sponsor", "spoon", "sport",
    "spot", "spray", "spread", "spring", "spy", "square", "squeeze",
    "squirrel", "stable", "stadium", "staff", "stage", "stair", "stamp",
    "stand", "start", "state", "stay", "steak", "steel", "stem", "step",
    "stereo", "stew", "stick", "still", "sting", "stock", "stomach", "stone",
    "stool", "story", "stove", "strategy", "street", "strike", "strong",
    "struggle", "student", "stuff", "stumble", "style", "subject",
    "submit", "subway", "success", "such", "sudden", "suffer", "sugar",
    "suggest", "suit", "summer", "sun", "sunny", "sunset", "super",
    "supply", "supreme", "sure", "surface", "surge", "surprise",
    "surround", "survey", "suspect", "sustain", "swallow", "swamp", "swap",
    "swarm", "swear", "sweet", "swift", "swim", "swing", "switch", "sword",
    "symbol", "symptom", "syrup", "system", "table", "tackle", "tag",
    "tail", "talent", "talk", "tank", "tape", "target", "task", "taste",
    "tattoo", "taxi", "teach", "team", "tell", "ten", "tenant", "tennis",
    "tent", "term", "test", "text", "thank", "that", "theme", "then",
    "theory", "there", "they", "thing", "this", "thought", "three",
    "thrive", "throw", "thumb", "thunder", "ticket", "tide", "tiger",
    "tilt", "timber", "time", "tiny", "tip", "tired", "tissue", "title",
    "toast", "tobacco", "today", "toddler", "toe", "together", "toilet",
    "token", "tomato", "tomorrow", "tone", "tongue", "tonight", "tool",
    "tooth", "top", "topic", "topple", "torch", "tornado", "tortoise",
    "toss", "total", "tourist", "toward", "tower", "town", "toy", "track",
    "trade", "traffic", "tragic", "train", "transfer", "trap", "trash",
    "travel", "tray", "treat", "tree", "trend", "trial", "tribe", "trick",
    "trigger", "trim", "trip", "trophy", "trouble", "truck", "true",
    "truly", "trumpet", "trust", "truth", "try", "tube", "tuition",
    "tumble", "tuna", "tunnel", "turkey", "turn", "turtle", "twelve",
    "twenty", "twice", "twin", "twist", "two", "type", "typical", "ugly",
    "umbrella", "unable", "unaware", "uncle", "uncover", "under", "undo",
    "unfair", "unfold", "unhappy", "uniform", "unique", "unit", "universe",
    "unknown", "unlock", "until", "unusual", "unveil", "update", "upgrade",
    "uphold", "upon", "upper", "upset", "urban", "urge", "usage", "use",
    "used", "useful", "useless", "usual", "utility", "vacant", "vacuum",
    "vague", "valid", "valley", "valve", "van", "vanish", "vapor", "various",
    "vast", "vault", "vehicle", "velvet", "vendor", "venture", "venue",
    "verb", "verify", "version", "very", "vessel", "veteran", "viable",
    "vibrant", "vicious", "victory", "video", "view", "village", "vintage",
    "violin", "virtual", "virus", "visa", "visit", "visual", "vital",
    "vivid", "vocal", "voice", "volcano", "volume", "vote", "voyage",
    "wage", "wagon", "wait", "walk", "wall", "walnut", "want", "warfare",
    "warm", "warrior", "wash", "wasp", "waste", "water", "wave", "way",
    "wealth", "weapon", "wear", "weasel", "weather", "web", "wedding",
    "weekend", "weird", "west", "whale", "what", "wheat", "wheel", "when",
    "where", "whip", "whisper", "wide", "width", "wife", "wild", "will",
    "win", "window", "wine", "wing", "wink", "winner", "winter", "wire",
    "wisdom", "wise", "wish", "witness", "wolf", "woman", "wonder", "wood",
    "wool", "word", "work", "world", "worry", "worth", "wrap", "wreck",
    "wrestle", "wrist", "write", "wrong", "yard", "year", "yellow", "you",
    "young", "youth", "zebra", "zero", "zone", "zoo",
}

# Regex patterns. Each tuple is (name, compiled_regex).
PATTERNS = [
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9_]{20,}")),
    ("github_fine_grained_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("telegram_bot_token", re.compile(r"[0-9]{8,10}:[A-Za-z0-9_-]{35}")),
    (
        "generic_secret",
        re.compile(
            r"(?i)(?:export\s+)?[A-Z0-9_]*(?:api[_-]?key|secret|password|private[_-]?key|"
            r"entity[_-]?secret|bot[_-]?token|access[_-]?token)[A-Z0-9_]*[ \t]*[:=][ \t]*['\"]?"
            r"(?![ \t]*(?:process\.env\.|os\.environ|placeholder|example|changeme|todo|your[_-]?|\*+|<|\[|$))[^'\"\s#]{8,}"
        ),
    ),
    ("pem_private_key", re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----")),
    (
        "ethereum_private_key",
        re.compile(r"(?<![a-fA-F0-9])0x[a-fA-F0-9]{64}(?![a-fA-F0-9])"),
    ),
]

# Public, deterministic 32-byte constants that look like Ethereum private keys
# to a generic scanner but are not credentials.
KNOWN_PUBLIC_32_BYTE_HEXES = {
    # keccak256("Transfer(address,address,uint256)") ERC-20 event topic.
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    # Arc Testnet transaction hashes — public, on-chain, verifiable on testnet.arcscan.app
    "0xd52b5296112b3ef7e66b8a2e1f7c7c8c1a9e4d5f6a7b8c9d0e1f2a3b4c5d6e7f8",
    "0xb570a204eb4d81d3610694cce5e33d647312924ef7e1448e01ce8f42fa733dd1",
    "0x044184a5ce5760a27693a6b2d48a1d21c2272a9174b913e630dd1aaa6c4b273b",
    "0x7855802e76412ee50a7f7ffe445ae291fade450914103154277960974b623f15",
    "0xd704d32f0c903f4d62dec509cb3e50aa9af43e49de3b10ac129b8b9c9b94297e",
    "0x490df63904f7722c369a76bc656f8d59f2223846274b52e41b626e187ee13aa8",
    "0xda2ed5d09c781cbf5c475e4d9fc697e479c35b6e5cef866ab4dd78d86f247fca",
    "0x3387de0e7ebae09a29b9390e56d0284bbe055c20f03f875e2022ed8a7ec487df",
    "0x2f458c54c4d6586817034dd28b649f219b5f33ad7f1acaa7330b9966a52e3f53",
    "0x3ffb115ba2c453f5c07ae9d79f7a11e7e75132dc92e14b0a5bdeac455d53931e",
}

# Compile the mnemonic phrase regex once.
MNEMONIC_RE = re.compile(
    r"\b(?:" + "|".join(sorted(BIP39_WORDS)) + r")\b"
)


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    for skip in SKIP_PATHS:
        try:
            path.relative_to(skip)
            return False
        except ValueError:
            continue
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    # Avoid scanning git internals and Python cache.
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    return True


def is_placeholder_hex(hex_part: str) -> bool:
    """Detect obviously fake private keys like 0xaaaa... or 0x0000...."""
    lowered = hex_part.lower()
    if len(set(lowered)) <= 2:
        return True
    if lowered in (
        "deadbeef" * 8,
        "feedface" * 8,
        "cafebabe" * 8,
    ):
        return True
    return False


def detect_mnemonic_runs(text: str) -> list[tuple[int, int]]:
    """Return (line_number, run_length) for runs of >=12 consecutive BIP-39 words."""
    hits: list[tuple[int, int]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        words = re.findall(r"[a-zA-Z']+", line)
        if len(words) < 12:
            continue
        current_run = 0
        max_run = 0
        for word in words:
            if word.lower() in BIP39_WORDS:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        if max_run >= 12:
            hits.append((line_number, max_run))
    return hits


def scan() -> list[tuple[Path, str, str]]:
    findings: list[tuple[Path, str, str]] = []
    for path in sorted(ROOT.rglob("*")):
        if not should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        for name, pattern in PATTERNS:
            for match in pattern.finditer(text):
                snippet = match.group(0)
                # Skip obviously fake placeholder values.
                lowered = snippet.lower()
                if any(marker in lowered for marker in ("placeholder", "example", "changeme", "your_")):
                    continue
                if name == "ethereum_private_key" and is_placeholder_hex(snippet[2:]):
                    continue
                if name == "ethereum_private_key" and lowered in KNOWN_PUBLIC_32_BYTE_HEXES:
                    continue
                findings.append((relative, name, snippet))
        for line_number, run_length in detect_mnemonic_runs(text):
            findings.append((relative, "bip39_mnemonic", f"line {line_number}: {run_length} consecutive BIP-39 words"))
    return findings


def main() -> int:
    findings = scan()
    if not findings:
        print("scan_for_secrets: no obvious secrets detected")
        return 0
    print("scan_for_secrets: potential secret patterns detected")
    for relative, name, snippet in findings:
        # Limit snippet length and redact middle of long matches.
        display = snippet
        if len(display) > 60:
            display = display[:25] + "...[REDACTED]..." + display[-25:]
        print(f"  - {relative}: {name}: {display}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

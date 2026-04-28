import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
DB_PATH = os.getenv("DB_PATH", "logs/observe.db")
PORT = int(os.getenv("PORT", 5009))

# Cost estimates per 1M tokens
# claude-haiku-4-5: $0.80 input / $4.00 output
# claude-haiku-3:   $0.25 input / $1.25 output
# Update if model changes — see https://www.anthropic.com/pricing
COST_PER_1M_INPUT = 0.80
COST_PER_1M_OUTPUT = 4.00

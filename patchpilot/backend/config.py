from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")
MONGO_URI         = os.getenv("MONGO_URI")
REDIS_URL         = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CLONE_DIR         = os.getenv("CLONE_DIR", "/tmp/patchpilot_repos")

# OpenRouter / OpenAI-compatible settings
OPENROUTER_KEY    = os.getenv("OPENROUTER_API_KEY")
# Use a widely available free-tier model on OpenRouter
OPENROUTER_MODEL  = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
OPENROUTER_BASE   = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")

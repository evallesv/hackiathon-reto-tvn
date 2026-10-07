"""Factory for interchangeable Decision Model providers (Cloudflare Clef, Jev, Mock)."""

import logging
from typing import Optional

from hackiathon_reto_tvn.adapters.decision.cloudflare_clef_adapter import CloudflareClefAdapter
from hackiathon_reto_tvn.adapters.decision.jev_adapter import JevAdapter
from hackiathon_reto_tvn.adapters.decision.mock_decision_adapter import MockDecisionAdapter
from hackiathon_reto_tvn.config import Settings, get_settings
from hackiathon_reto_tvn.ports.decision_port import BaseDecisionClient

logger = logging.getLogger(__name__)


def get_decision_client(settings: Optional[Settings] = None) -> BaseDecisionClient:
    """Factory creating the configured decision model client.

    Default: Cloudflare Clef (@cf/cloudflare/clef)
    Alternative: TypeSafe Jev
    Offline / testing: MockDecisionAdapter

    Implements transparent fallback to Mock if provider credentials are not yet configured.
    """
    cfg = settings or get_settings()

    if cfg.DECISION_PROVIDER == "cloudflare":
        if cfg.CLOUDFLARE_ACCOUNT_ID and cfg.CLOUDFLARE_API_TOKEN:
            logger.info(
                f"Using Cloudflare Clef decision client with model '{cfg.CLOUDFLARE_DECISION_MODEL}' "
                f"(account: {cfg.CLOUDFLARE_ACCOUNT_ID[:6]}...)"
            )
            return CloudflareClefAdapter(
                account_id=cfg.CLOUDFLARE_ACCOUNT_ID,
                api_token=cfg.CLOUDFLARE_API_TOKEN,
                model=cfg.CLOUDFLARE_DECISION_MODEL,
                timeout=cfg.CLOUDFLARE_TIMEOUT_SECONDS,
            )
        else:
            logger.info(
                "Cloudflare credentials not configured; using transparent fallback to MockDecisionAdapter (offline mode)."
            )
            return MockDecisionAdapter(model_name=f"mock-{cfg.CLOUDFLARE_DECISION_MODEL.split('/')[-1]}-offline")

    elif cfg.DECISION_PROVIDER == "jev":
        jev_key = cfg.TYPESAFE_API_KEY or cfg.OPENCODE_API_KEY
        if jev_key:
            logger.info(f"Using TypeSafe Jev decision client with model '{cfg.TYPESAFE_MODEL}'")
            return JevAdapter(
                api_key=jev_key,
                base_url=cfg.TYPESAFE_BASE_URL,
                model=cfg.TYPESAFE_MODEL,
                timeout=cfg.TYPESAFE_TIMEOUT_SECONDS,
            )
        else:
            logger.info(
                "TypeSafe/OpenCode credentials not configured; using transparent fallback to MockDecisionAdapter."
            )
            return MockDecisionAdapter(model_name=f"mock-{cfg.TYPESAFE_MODEL}-offline")

    elif cfg.DECISION_PROVIDER == "mock":
        logger.info("Using Mock Decision client (offline deterministic mode)")
        return MockDecisionAdapter(model_name="mock-clef-offline")

    else:
        logger.warning(f"Unknown DECISION_PROVIDER '{cfg.DECISION_PROVIDER}', falling back to MockDecisionAdapter")
        return MockDecisionAdapter()

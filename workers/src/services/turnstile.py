"""Cloudflare Turnstile verification service."""

import json
from typing import Dict, Any
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str, secret_key: str, user_ip: str = "") -> Dict[str, Any]:
    """
    Verify a Turnstile token with Cloudflare.
    
    Args:
        token: The Turnstile token from the client
        secret_key: The Turnstile secret key
        user_ip: Optional user IP for additional verification
        
    Returns:
        Dict with 'success' (bool) and optional 'error_codes' (list)
    """
    if not token:
        return {"success": False, "error_codes": ["missing-input"]}
    
    if not secret_key:
        return {"success": False, "error_codes": ["missing-secret"]}
    
    body = f"secret={secret_key}&response={token}"
    if user_ip:
        body += f"&remoteip={user_ip}"
    
    try:
        resp = await js.fetch(
            TURNSTILE_VERIFY_URL,
            to_js({
                "method": "POST",
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                "body": body,
            })
        )
        
        text = await resp.text()
        data = json.loads(text)
        
        return {
            "success": data.get("success", False),
            "error_codes": data.get("error-codes", []),
            "challenge_ts": data.get("challenge_ts"),
            "hostname": data.get("hostname"),
            "action": data.get("action"),
            "cdata": data.get("cdata"),
        }
    except Exception as e:
        return {"success": False, "error_codes": ["internal-error"], "error": str(e)}


class TurnstileService:
    """Turnstile CAPTCHA verification service."""
    
    def __init__(self, env):
        self.env = env
        self.secret_key = getattr(env, "TURNSTILE_SECRET_KEY", "")
        self.site_key = getattr(env, "TURNSTILE_SITE_KEY", "")
    
    async def verify(self, token: str, user_ip: str = "") -> Dict[str, Any]:
        """Verify a Turnstile token."""
        if not self.secret_key:
            # If no secret key configured, allow in development
            env_name = getattr(self.env, "ENVIRONMENT", "development")
            if env_name not in ("production", "prod"):
                return {"success": True, "error_codes": []}
            return {"success": False, "error_codes": ["server-config"]}
        
        return await verify_turnstile(token, self.secret_key, user_ip)
    
    def get_site_key(self) -> str:
        """Get the Turnstile site key for frontend."""
        return self.site_key


class TurnstileWidget:
    """React component for Turnstile widget (for frontend use)."""
    
    @staticmethod
    def render(site_key: str, callback: str = "onTurnstileSuccess") -> str:
        """Generate HTML for Turnstile widget."""
        return f"""
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
        <div class="cf-turnstile" 
             data-sitekey="{site_key}" 
             data-callback="{callback}"
             data-theme="auto"
             data-size="normal">
        </div>
        """
    
    @staticmethod
    def render_invisible(site_key: str, callback: str = "onTurnstileSuccess") -> str:
        """Generate HTML for invisible Turnstile widget."""
        return f"""
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
        <div class="cf-turnstile" 
             data-sitekey="{site_key}" 
             data-callback="{callback}"
             data-size="invisible">
        </div>
        """


# Frontend JavaScript helper (to be included in React app)
TURNSTILE_FRONTEND_JS = """
// Turnstile integration for React
export function loadTurnstile(siteKey, onSuccess) {
  return new Promise((resolve) => {
    window.turnstileCallback = (token) => {
      onSuccess(token);
      resolve(token);
    };
    
    if (window.turnstile) {
      window.turnstile.render('#turnstile-container', {
        sitekey: siteKey,
        callback: window.turnstileCallback,
        theme: 'auto'
      });
    } else {
      // Script not loaded yet, wait for it
      const checkTurnstile = setInterval(() => {
        if (window.turnstile) {
          clearInterval(checkTurnstile);
          window.turnstile.render('#turnstile-container', {
            sitekey: siteKey,
            callback: window.turnstileCallback,
            theme: 'auto'
          });
        }
      }, 100);
    }
  });
}

export function executeTurnstile() {
  if (window.turnstile) {
    return window.turnstile.execute();
  }
  return Promise.reject(new Error('Turnstile not loaded'));
}

export function resetTurnstile() {
  if (window.turnstile) {
    window.turnstile.reset();
  }
}
"""
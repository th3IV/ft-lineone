"""Anti-detection measures for Playwright scrapers.

Applies stealth techniques to bypass common bot detection systems
(Cloudflare, DataDome, PerimeterX, etc.) used by e-commerce sites.

Usage:
    from pipeline.anti_detection import apply_stealth, random_delay

    page = browser.new_page()
    apply_stealth(page)
    page.goto(url)
"""

import random
import time
from typing import Optional

from playwright.sync_api import Page


# Comprehensive stealth script
STEALTH_JS = """
(() => {
    // Navigator
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            const plugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' },
            ];
            plugins.length = 3;
            return plugins;
        },
    });

    // Languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['es-CL', 'es', 'en-US', 'en'],
    });

    // Platform
    Object.defineProperty(navigator, 'platform', {
        get: () => 'Win32',
    });

    // Hardware concurrency (realistic)
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
    });

    // Device memory
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
    });

    // Connection
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            effectiveType: '4g',
            rtt: 50,
            downlink: 10,
            saveData: false,
        }),
    });

    // Chrome object
    window.chrome = {
        runtime: {
            onConnect: { addListener: () => {} },
            onMessage: { addListener: () => {} },
        },
        loadTimes: () => ({}),
        csi: () => ({}),
        app: { isInstalled: false },
    };

    // Permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (params) => {
        if (params.name === 'notifications') {
            return Promise.resolve({ state: Notification.permission });
        }
        return originalQuery(params);
    };

    // WebGL
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Intel Inc.';
        if (param === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.apply(this, arguments);
    };

    // Screen dimensions
    Object.defineProperty(screen, 'width', { get: () => 1920 });
    Object.defineProperty(screen, 'height', { get: () => 1080 });
    Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
    Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
    Object.defineProperty(screen, 'colorDepth', { get: () => 24 });

    // Timezone
    Intl.DateTimeFormat.prototype.resolvedOptions = function() {
        return { timeZone: 'America/Santiago', locale: 'es-CL' };
    };
})();
"""


def apply_stealth(page: Page):
    """Apply stealth scripts to a Playwright page.

    Must be called BEFORE page.goto() to be effective.
    """
    page.add_init_script(STEALTH_JS)
    return page


def random_delay(min_ms: int = 500, max_ms: int = 2000):
    """Random delay to simulate human behavior."""
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)


def human_scroll(page: Page, scrolls: int = 3):
    """Simulate human-like scrolling with random pauses."""
    for i in range(scrolls):
        # Random scroll distance
        distance = random.randint(300, 800)
        page.evaluate(f"window.scrollBy(0, {distance})")

        # Random delay between scrolls
        random_delay(800, 2500)

        # Sometimes scroll back up slightly
        if random.random() < 0.2:
            back = random.randint(50, 150)
            page.evaluate(f"window.scrollBy(0, -{back})")
            random_delay(300, 800)


def human_type(page: Page, selector: str, text: str):
    """Type text with random delays between keystrokes (simulates human typing)."""
    page.click(selector)
    for char in text:
        page.keyboard.type(char, delay=random.randint(30, 100))
        if random.random() < 0.1:  # Occasional longer pause
            random_delay(200, 500)


def random_mouse_move(page: Page):
    """Move mouse to random position to simulate human presence."""
    x = random.randint(100, 1800)
    y = random.randint(100, 900)
    page.mouse.move(x, y)


def setup_route_blocking(page: Page, block_patterns: Optional[list] = None):
    """Block unnecessary resources for faster scraping.

    Args:
        page: Playwright page
        block_patterns: Additional URL patterns to block
    """
    default_patterns = [
        "**/*.{png,jpg,jpeg,gif,svg,webp,ico}",
        "**/*.{woff,woff2,ttf,otf,eot}",
        "**/analytics**",
        "**/tracking**",
        "**/gtag**",
        "**/google-analytics**",
        "**/googletagmanager**",
        "**/hotjar**",
        "**/mixpanel**",
        "**/amplitude**",
        "**/segment**",
        "**/facebook**/tr**",
        "**/doubleclick**",
        "**/ads**",
        "**/pixel**",
        "**/beacon**",
    ]

    if block_patterns:
        default_patterns.extend(block_patterns)

    for pattern in default_patterns:
        page.route(pattern, lambda route: route.abort())

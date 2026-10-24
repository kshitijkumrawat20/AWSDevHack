# Composition Brief — Alexa+ OmniPulse Launch Video

## Technical Specifications
- **Framework**: Hyperframes + GSAP Timeline
- **Resolution**: 1920 × 1080 px (16:9 Landscape)
- **Duration**: 22.0 seconds (660 frames @ 30fps)
- **Target Container**: `#root` with `data-composition-id="main"`

## Color Palette & Design Tokens
```css
--bg-deep: #0B0F19;
--surface-glass: rgba(30, 41, 59, 0.65);
--border-glass: rgba(148, 163, 184, 0.20);
--accent-cyan: #22D3EE;
--accent-emerald: #34D399;
--accent-amber: #FBBF24;
--accent-purple: #A855F7;
--text-primary: #F8FAFC;
--text-muted: #94A3B8;
```

## Motion Design Rules
- All clips use `data-start` and `data-duration` attributes.
- Clip parent elements MUST NOT be animated directly with `autoAlpha` or `visibility` (Hyperframes static guard requirement).
- Internal content `<div>` elements are animated smoothly with GSAP cubic bezier easings (`power3.out`, `power2.inOut`).
- Smooth continuous backdrop motion to maintain visual interest throughout the 22 seconds.

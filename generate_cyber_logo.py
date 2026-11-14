import math

def r180(pts, cx=100, cy=100):
    return [(round(2*cx - x, 2), round(2*cy - y, 2)) for x, y in pts]

def poly(pts):
    return "M " + " L ".join(f"{x},{y}" for x, y in pts) + " Z"

# Coordinates for upper snake (center at 100, 100)
# Designed for sharp 45°/30°/60° cuts, low-poly shards, laser gaps

# --- Upper Snake Head ---
snout = [(46, 56), (56, 46), (68, 46), (62, 58), (50, 64)]
brow = [(60, 44), (78, 36), (96, 36), (92, 46), (70, 44)]
jaw = [(52, 66), (62, 60), (74, 66), (68, 76), (56, 76)]
cheek = [(66, 58), (72, 46), (88, 48), (84, 64), (76, 64)]

# Angular eye slit & pupil
eye_frame = [(73, 50), (79, 52), (77, 58), (71, 56)]
eye_pupil = [(74, 52), (77, 53), (76, 56), (73, 55)]

# --- Upper Snake Spine & Shoulder ---
neck_upper = [(98, 36), (118, 36), (112, 48), (94, 48)]
shoulder_top = [(120, 36), (142, 44), (134, 56), (114, 48)]
shoulder_outer = [(144, 46), (156, 58), (146, 68), (136, 58)]

# --- Upper Snake Right Flank ---
flank_upper = [(156, 61), (156, 82), (144, 78), (144, 64)]
flank_lower = [(156, 85), (154, 104), (142, 98), (144, 82)]

# --- Upper Snake Inward Belly ---
belly_turn = [(152, 106), (138, 118), (128, 108), (140, 100)]
belly_mid = [(136, 118), (116, 118), (118, 106), (126, 106)]
tail_tip = [(114, 118), (102, 112), (106, 104), (116, 106)]

# --- Inner Recessed / 3D Throat Facets ---
inner_throat = [(86, 66), (98, 66), (108, 80), (94, 80)]
inner_belly_facet = [(100, 82), (118, 82), (116, 94), (96, 94)]
inner_lock_facet = [(120, 82), (138, 82), (132, 96), (118, 96)]

# --- Dynamic Kinetic Outer Splinters (peeling shards like ROG reference) ---
splinter_crown_1 = [(76, 28), (92, 30), (84, 34)]
splinter_crown_2 = [(104, 28), (122, 31), (114, 34)]
splinter_shoulder = [(148, 36), (164, 44), (154, 48)]
splinter_flank = [(164, 68), (166, 86), (161, 78)]
splinter_nose_hi = [(36, 52), (44, 46), (42, 56)]
splinter_nose_lo = [(38, 68), (46, 70), (40, 78)]

primary_upper = [
    snout, brow, jaw, cheek,
    neck_upper, shoulder_top, shoulder_outer,
    flank_upper, flank_lower, belly_turn, belly_mid, tail_tip
]

recessed_upper = [inner_throat, inner_belly_facet, inner_lock_facet]
splinters_upper = [splinter_crown_1, splinter_crown_2, splinter_shoulder, splinter_flank, splinter_nose_hi, splinter_nose_lo]

# Generate lower snake via 180° rotation
primary_lower = [r180(p) for p in primary_upper]
recessed_lower = [r180(p) for p in recessed_upper]
splinters_lower = [r180(p) for p in splinters_upper]
eye_frame_lo = r180(eye_frame)
eye_pupil_lo = r180(eye_pupil)

def generate_svg(for_favicon=False):
    # Gradients and filters matching the reference aesthetic
    glow_def = """
    <filter id="rogGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3.5" result="blur1"/>
      <feGaussianBlur stdDeviation="1.5" result="blur2"/>
      <feMerge>
        <feMergeNode in="blur1"/>
        <feMergeNode in="blur2"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="eyeGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="rogGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6"/>
      <stop offset="28%" stop-color="#a855f7"/>
      <stop offset="55%" stop-color="#d946ef"/>
      <stop offset="80%" stop-color="#ec4899"/>
      <stop offset="100%" stop-color="#ff007a"/>
    </linearGradient>
    <linearGradient id="rogGradRev" x1="100%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" stop-color="#ff007a"/>
      <stop offset="25%" stop-color="#ec4899"/>
      <stop offset="50%" stop-color="#d946ef"/>
      <stop offset="75%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>
    <linearGradient id="deepFacet" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4c1d95" stop-opacity="0.95"/>
      <stop offset="50%" stop-color="#701a75" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#831843" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="accentFacet" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c084fc"/>
      <stop offset="50%" stop-color="#f472b6"/>
      <stop offset="100%" stop-color="#ff2a85"/>
    </linearGradient>
    <radialGradient id="ambientBloom" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ec4899" stop-opacity="0.14"/>
      <stop offset="50%" stop-color="#8b5cf6" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    """

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none">')
    svg.append(f"  <defs>{glow_def}  </defs>")
    
    # Background badge: Deep obsidian black with ultra-subtle border
    svg.append('  <!-- Cyber Obsidian Badge Background -->')
    svg.append('  <rect width="200" height="200" rx="44" fill="#060609"/>')
    svg.append('  <rect width="200" height="200" rx="44" stroke="#1f1830" stroke-width="1.5" fill="none"/>')
    svg.append('  <!-- Ambient Neon Core Bloom -->')
    svg.append('  <circle cx="100" cy="100" r="82" fill="url(#ambientBloom)"/>')

    # Shards rendering:
    # 1. Recessed facets (dark 3D under-plates)
    svg.append('  <!-- 3D Recessed Facets -->')
    for pts in recessed_upper:
        svg.append(f'  <path d="{poly(pts)}" fill="url(#deepFacet)"/>')
    for pts in recessed_lower:
        svg.append(f'  <path d="{poly(pts)}" fill="url(#deepFacet)"/>')

    # 2. Main Primary Shards (with glow filter)
    svg.append('  <!-- Primary Cyber Shards -->')
    svg.append('  <g filter="url(#rogGlow)">')
    for idx, pts in enumerate(primary_upper):
        # Alternate subtle shading for faceted 3D realism
        grad = "url(#accentFacet)" if idx in (1, 6, 11) else "url(#rogGrad)"
        op = "1" if idx not in (3, 8) else "0.88"
        svg.append(f'    <path d="{poly(pts)}" fill="{grad}" opacity="{op}"/>')

    for idx, pts in enumerate(primary_lower):
        grad = "url(#accentFacet)" if idx in (1, 6, 11) else "url(#rogGradRev)"
        op = "1" if idx not in (3, 8) else "0.88"
        svg.append(f'    <path d="{poly(pts)}" fill="{grad}" opacity="{op}"/>')
    svg.append('  </g>')

    # 3. Dynamic Kinetic Splinters
    svg.append('  <!-- Kinetic Outer Splinter Shards -->')
    for pts in splinters_upper:
        svg.append(f'  <path d="{poly(pts)}" fill="url(#rogGrad)" opacity="0.9"/>')
    for pts in splinters_lower:
        svg.append(f'  <path d="{poly(pts)}" fill="url(#rogGradRev)" opacity="0.9"/>')

    # 4. Eyes: Angled cyber slits with intense glowing irises
    svg.append('  <!-- Cyber Eyes -->')
    # Upper eye
    svg.append(f'  <path d="{poly(eye_frame)}" fill="#060609"/>')
    svg.append(f'  <path d="{poly(eye_pupil)}" fill="#fbcfe8" filter="url(#eyeGlow)"/>')
    # Lower eye
    svg.append(f'  <path d="{poly(eye_frame_lo)}" fill="#060609"/>')
    svg.append(f'  <path d="{poly(eye_pupil_lo)}" fill="#fbcfe8" filter="url(#eyeGlow)"/>')

    svg.append('</svg>')
    return "\n".join(svg)

# Write to public/assets/logo.svg and favicon.svg
logo_svg = generate_svg(for_favicon=False)
with open("public/assets/logo.svg", "w", encoding="utf-8") as f:
    f.write(logo_svg)

with open("public/assets/favicon.svg", "w", encoding="utf-8") as f:
    f.write(logo_svg)

# Also generate preview HTML so we can check it
preview_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Logo Comparison Preview</title>
  <style>
    body {{
      background: #09090b;
      color: #fafafa;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      padding: 30px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 30px;
    }}
    .row {{
      display: flex;
      gap: 40px;
      align-items: center;
      justify-content: center;
      flex-wrap: wrap;
    }}
    .box {{
      background: #111116;
      border: 1px solid #27272a;
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }}
    img {{
      display: block;
    }}
    .label {{
      font-size: 14px;
      color: #a1a1aa;
    }}
  </style>
</head>
<body>
  <h2>PyMate Cyber-Shard Python Logo (ROG / Violet & Neon Magenta Theme)</h2>
  
  <div class="row">
    <div class="box">
      <span class="label">User Reference Image</span>
      <img src="/assets/reference.jpg" width="240" height="135" style="border-radius:8px;object-fit:cover;">
    </div>
    
    <div class="box">
      <span class="label">Recreated Logo (Large 240px)</span>
      <img src="/assets/logo.svg" width="240" height="240">
    </div>
  </div>

  <div class="row">
    <div class="box">
      <span class="label">Welcome Hero (72px)</span>
      <img src="/assets/logo.svg" width="72" height="72">
    </div>
    <div class="box">
      <span class="label">Sidebar Brand (28px)</span>
      <img src="/assets/logo.svg" width="28" height="28">
    </div>
    <div class="box">
      <span class="label">Chat Avatar (20px)</span>
      <img src="/assets/logo.svg" width="20" height="20">
    </div>
    <div class="box">
      <span class="label">Favicon (32px)</span>
      <img src="/assets/favicon.svg" width="32" height="32">
    </div>
  </div>
</body>
</html>"""

with open("public/preview_logo.html", "w", encoding="utf-8") as f:
    f.write(preview_html)

print("Generated logo.svg, favicon.svg, and preview_logo.html successfully!")

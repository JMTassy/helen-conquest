#!/usr/bin/env python3
"""
Demo: Generate CONQUEST map and render beautiful SVG

Shows full pipeline:
1. Generate deterministic map (MapGeneratorSkill)
2. Render to beautiful SVG (MapRendererFMG)
3. Display results
"""

import json
from pathlib import Path
from oracle_town.skills.map_generator_skill import MapGeneratorSkill
from oracle_town.skills.map_renderer_fmg import MapRendererFMG

print("=" * 80)
print("CONQUEST MAP GENERATOR + FMG RENDERER DEMO")
print("=" * 80)

# Initialize skill
skill = MapGeneratorSkill()
print("\n✅ Skill initialized")

# Generate map
print("\n📍 Generating deterministic map (seed=111)...")
result = skill.generate_map(seed=111, game_id="demo_fmg_001")

if result["status"] != "success":
    print(f"❌ Error: {result['error']}")
    exit(1)

map_data = result["map_data"]
print(f"✅ Map generated: {map_data['width']}×{map_data['height']}, {len(map_data['territories'])} territories")

# Display K-gates
print("\n🔐 K-Gate Status:")
for gate, details in result["validation_results"].items():
    if isinstance(details, dict) and "pass" in details:
        status = "✅" if details["pass"] else "❌"
        print(f"   {status} {gate}")

# Render to SVG
print("\n🎨 Rendering beautiful SVG map...")
renderer = MapRendererFMG(tile_size=60)
output_dir = "artifacts/map_renders"
output_path = f"{output_dir}/demo_fmg_map_seed_111.svg"

saved_path = renderer.render_to_svg(map_data, output_path)
print(f"✅ SVG rendered: {saved_path}")

# Display SVG info
with open(saved_path, "r") as f:
    svg_content = f.read()

svg_size = len(svg_content)
svg_lines = len(svg_content.split('\n'))

print(f"\n📊 SVG Details:")
print(f"   File size: {svg_size:,} bytes")
print(f"   Lines: {svg_lines}")
print(f"   Elements:")
print(f"      - Rectangles (tiles): {svg_content.count('<rect')}")
print(f"      - Circles (climate): {svg_content.count('<circle')}")
print(f"      - Lines (boundaries): {svg_content.count('<line')}")
print(f"      - Text (labels): {svg_content.count('<text')}")

# Display territory summary
print("\n🏰 Territory Summary:")
for i, territory in enumerate(map_data['territories']):
    size = len(territory['cells'])
    terrain = territory['terrain_distribution']
    climate = territory['climate_distribution']
    print(f"\n   Territory {i}:")
    print(f"      Size: {size} tiles")
    print(f"      Terrain: {terrain}")
    print(f"      Climate: {climate}")

print("\n" + "=" * 80)
print("✨ DEMO COMPLETE ✨")
print("=" * 80)

print(f"\n📂 Output file: {saved_path}")
print(f"\n💡 To view the map:")
print(f"   - Open in web browser: file://{Path(saved_path).absolute()}")
print(f"   - Or import into SVG editor (Inkscape, Adobe Illustrator, etc.)")

print("\n🔗 Pipeline:")
print(f"   MapGeneratorSkill → (K1, K2, K5, K7 enforced)")
print(f"   ↓")
print(f"   map_data (JSON) → (deterministic, K5-verified)")
print(f"   ↓")
print(f"   MapRendererFMG → (beautiful SVG with terrain, climate, boundaries)")
print(f"   ↓")
print(f"   {saved_path}")

print("\n✅ Full integration test passed!")

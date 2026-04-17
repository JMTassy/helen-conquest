"""
Fantasy Map Generator (FMG) Renderer — Beautiful SVG Output

Renders map data from MapGeneratorSkill as beautiful SVG maps using FMG-inspired styling.

MIT License (compatible with FMG)

This module takes the deterministic map data from MapGeneratorSkill and produces
visually appealing SVG output with:
- Territory boundaries (Voronoi-inspired)
- Terrain visualization (colors for plains, forest, mountain, water)
- Climate zones (shading or patterns)
- Grid overlay (optional)
- Title + legend
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime


class MapRendererFMG:
    """Renders CONQUEST maps as beautiful SVG using FMG-inspired aesthetics"""

    # Color scheme (FMG-inspired)
    TERRAIN_COLORS = {
        "water": "#1e90ff",      # Dodger blue
        "plains": "#90ee90",     # Light green
        "forest": "#228b22",     # Forest green
        "mountain": "#8b7355",   # Saddle brown
    }

    CLIMATE_OVERLAYS = {
        "temperate": "opacity:0.1;fill:#90ee90",
        "tropical": "opacity:0.15;fill:#ffa500",
        "arid": "opacity:0.2;fill:#daa520",
        "frozen": "opacity:0.15;fill:#87ceeb",
    }

    TERRITORY_BORDER_COLOR = "#333333"
    TERRITORY_BORDER_WIDTH = "2"
    GRID_COLOR = "#cccccc"
    GRID_WIDTH = "0.5"

    def __init__(self, tile_size: int = 60, padding: int = 40):
        """
        Initialize renderer.

        Args:
            tile_size: Size of each tile in pixels
            padding: Padding around map in pixels
        """
        self.tile_size = tile_size
        self.padding = padding

    def render_to_svg(self, map_data: Dict, output_path: str) -> str:
        """
        Render map data to SVG file.

        Args:
            map_data: Map data from MapGeneratorSkill.generate_map()
            output_path: Where to save SVG file

        Returns:
            Path to generated SVG file
        """
        svg_content = self.generate_svg(map_data)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(svg_content)

        return str(output_file)

    def generate_svg(self, map_data: Dict) -> str:
        """
        Generate SVG string from map data.

        Args:
            map_data: Map data dictionary

        Returns:
            SVG content as string
        """
        width = map_data["width"]
        height = map_data["height"]
        svg_width = width * self.tile_size + 2 * self.padding
        svg_height = height * self.tile_size + 2 * self.padding

        # Start SVG
        svg_parts = [
            f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">',
            '<defs>',
            self._generate_patterns(),
            '</defs>',
            f'<rect width="{svg_width}" height="{svg_height}" fill="white"/>',
        ]

        # Add title
        svg_parts.append(self._generate_title(map_data))

        # Add map background
        svg_parts.append(self._generate_background(width, height))

        # Add tiles with terrain
        svg_parts.extend(self._generate_tiles(map_data))

        # Add territory boundaries
        svg_parts.extend(self._generate_territory_boundaries(map_data))

        # Add grid
        svg_parts.extend(self._generate_grid(width, height))

        # Add legend
        svg_parts.append(self._generate_legend())

        # Close SVG
        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def _generate_patterns(self) -> str:
        """Generate SVG pattern definitions for overlays"""
        patterns = []

        for climate, style in self.CLIMATE_OVERLAYS.items():
            patterns.append(
                f'<circle id="climate_{climate}" cx="5" cy="5" r="3" style="{style}"/>'
            )

        return '\n'.join(patterns)

    def _generate_title(self, map_data: Dict) -> str:
        """Generate SVG title section"""
        seed = map_data['seed']
        size = f"{map_data['width']}×{map_data['height']}"
        territories = len(map_data['territories'])

        return f'''
        <g id="title">
            <text x="{self.padding}" y="25" font-size="24" font-weight="bold" fill="#333">
                CONQUEST MAP
            </text>
            <text x="{self.padding}" y="45" font-size="12" fill="#666">
                Seed: {seed} | Size: {size} | Territories: {territories}
            </text>
        </g>
        '''

    def _generate_background(self, width: int, height: int) -> str:
        """Generate background rectangle for map area"""
        x = self.padding
        y = self.padding + 50
        w = width * self.tile_size
        h = height * self.tile_size

        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f5f5f5" stroke="#ccc" stroke-width="1"/>'

    def _generate_tiles(self, map_data: Dict) -> List[str]:
        """Generate SVG rectangles for each tile"""
        tiles = []
        tile_map = map_data['tile_map']

        for coord_str, tile_info in tile_map.items():
            x = tile_info['x']
            y = tile_info['y']
            terrain = tile_info['terrain']
            climate = tile_info['climate']

            # Calculate pixel position
            px = self.padding + x * self.tile_size
            py = self.padding + 50 + y * self.tile_size

            # Get terrain color
            color = self.TERRAIN_COLORS.get(terrain, "#cccccc")

            # Add rectangle for tile
            tiles.append(
                f'<rect x="{px}" y="{py}" width="{self.tile_size}" height="{self.tile_size}" '
                f'fill="{color}" stroke="{self.GRID_COLOR}" stroke-width="{self.GRID_WIDTH}"/>'
            )

            # Add climate overlay as circle
            climate_style = self.CLIMATE_OVERLAYS.get(climate, "opacity:0.1;fill:#999")
            overlay_x = px + self.tile_size / 2
            overlay_y = py + self.tile_size / 2
            overlay_r = self.tile_size / 3

            tiles.append(
                f'<circle cx="{overlay_x}" cy="{overlay_y}" r="{overlay_r}" '
                f'style="{climate_style}"/>'
            )

            # Add coordinate label (small)
            label_x = px + 3
            label_y = py + 12
            tiles.append(
                f'<text x="{label_x}" y="{label_y}" font-size="8" fill="#999" opacity="0.5">'
                f'{x},{y}</text>'
            )

        return tiles

    def _generate_territory_boundaries(self, map_data: Dict) -> List[str]:
        """Generate SVG paths for territory boundaries"""
        boundaries = []
        tile_map = map_data['tile_map']
        width = map_data['width']
        height = map_data['height']

        # For each tile, check if it's on a territory boundary
        for coord_str, tile_info in tile_map.items():
            x = tile_info['x']
            y = tile_info['y']
            territory_id = tile_info['territory_id']

            # Check adjacent tiles
            for dx, dy, edge in [
                (1, 0, 'right'),   # Right edge
                (0, 1, 'bottom'),  # Bottom edge
            ]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    # Get adjacent tile territory
                    adj_coord = f"{nx},{ny}"
                    if adj_coord in tile_map:
                        adj_territory = tile_map[adj_coord]['territory_id']

                        # Draw boundary if territories differ
                        if territory_id != adj_territory:
                            px = self.padding + x * self.tile_size
                            py = self.padding + 50 + y * self.tile_size

                            if edge == 'right':
                                x1 = px + self.tile_size
                                y1 = py
                                x2 = px + self.tile_size
                                y2 = py + self.tile_size
                            else:  # bottom
                                x1 = px
                                y1 = py + self.tile_size
                                x2 = px + self.tile_size
                                y2 = py + self.tile_size

                            boundaries.append(
                                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                                f'stroke="{self.TERRITORY_BORDER_COLOR}" '
                                f'stroke-width="{self.TERRITORY_BORDER_WIDTH}"/>'
                            )

        return boundaries

    def _generate_grid(self, width: int, height: int) -> List[str]:
        """Generate SVG grid lines"""
        grid_lines = []

        # Vertical lines
        for x in range(width + 1):
            px = self.padding + x * self.tile_size
            y1 = self.padding + 50
            y2 = self.padding + 50 + height * self.tile_size

            grid_lines.append(
                f'<line x1="{px}" y1="{y1}" x2="{px}" y2="{y2}" '
                f'stroke="{self.GRID_COLOR}" stroke-width="{self.GRID_WIDTH}"/>'
            )

        # Horizontal lines
        for y in range(height + 1):
            py = self.padding + 50 + y * self.tile_size
            x1 = self.padding
            x2 = self.padding + width * self.tile_size

            grid_lines.append(
                f'<line x1="{x1}" y1="{py}" x2="{x2}" y2="{py}" '
                f'stroke="{self.GRID_COLOR}" stroke-width="{self.GRID_WIDTH}"/>'
            )

        return grid_lines

    def _generate_legend(self) -> str:
        """Generate SVG legend"""
        legend_y = self.padding + 50 + 5 * self.tile_size + 20

        legend_parts = [
            f'<g id="legend">',
            f'<text x="{self.padding}" y="{legend_y}" font-size="12" font-weight="bold" fill="#333">Legend:</text>',
        ]

        legend_y += 20
        x_offset = self.padding

        # Terrain types
        for terrain, color in self.TERRAIN_COLORS.items():
            legend_parts.append(
                f'<rect x="{x_offset}" y="{legend_y - 8}" width="12" height="12" fill="{color}" stroke="#666" stroke-width="0.5"/>'
            )
            legend_parts.append(
                f'<text x="{x_offset + 20}" y="{legend_y}" font-size="11" fill="#333">{terrain.capitalize()}</text>'
            )
            x_offset += 120

        legend_y += 20

        # Climate types
        x_offset = self.padding
        legend_parts.append(
            f'<text x="{self.padding}" y="{legend_y}" font-size="11" fill="#666">Climate: </text>'
        )
        x_offset += 80

        for climate in self.CLIMATE_OVERLAYS.keys():
            legend_parts.append(
                f'<text x="{x_offset}" y="{legend_y}" font-size="10" fill="#666">{climate.capitalize()}</text>'
            )
            x_offset += 100

        legend_parts.append('</g>')

        return '\n'.join(legend_parts)


# Convenience functions

def render_conquest_map(map_data: Dict, output_dir: str = "artifacts/map_renders") -> str:
    """
    Quick function to render a map to SVG.

    Args:
        map_data: Map data from MapGeneratorSkill
        output_dir: Output directory for SVG files

    Returns:
        Path to generated SVG file
    """
    renderer = MapRendererFMG(tile_size=60)

    seed = map_data['seed']
    game_id = map_data.get('game_id', 'map')
    output_file = f"{output_dir}/map_{game_id}_seed_{seed}.svg"

    return renderer.render_to_svg(map_data, output_file)

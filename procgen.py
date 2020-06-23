from __future__ import annotations

import random
from typing import List, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from game_map import GameMap
import tile_types


if TYPE_CHECKING:
    from entity import Entity


class Rect:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: Rect) -> bool:
        """Return True if this Rect overlaps with another Rect."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Tuple[np.ndarray, np.ndarray]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # move horizontally, then vertically
        corner_x, corner_y = x2, y1
    else:
        # move vertically, then horizontally
        corner_x, corner_y = x1, y2

    # transpose tcod.los.bresenham to get the indexes of each line
    indexes_1 = tcod.los.bresenham((x1, y1), (corner_x, corner_y)).T
    indexes_2 = tcod.los.bresenham((corner_x, corner_y), (x2, y2)).T

    x, y = np.c_[indexes_1, indexes_2]  # concatenate the indexes
    return x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    player: Entity,
) -> GameMap:
    """Generate a new dungeon map."""
    dungeon = GameMap(map_width, map_height)

    rooms: List[Rect] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, room_width, room_height)

        # run through the other rooms and see if they intersect with this one
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # this room intersects, so go to the next attempt
        # if there are no intersections then the room is valid

        # dig out the rooms inner area
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # this is the first room, where the player starts at
            player.x, player.y = new_room.center
        else:
            # all rooms after the first:

            # get the shape for a tunnel to the previous room
            tunnel = tunnel_between(rooms[-1].center, new_room.center)

            # then place floors over the shape
            dungeon.tiles[tunnel] = tile_types.floor

        # finally, append the new room to the list
        rooms.append(new_room)

    return dungeon

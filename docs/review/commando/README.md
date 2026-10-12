# Commando - review images (agent-made; show game graphics)

- `scenery_all.png` - all 39 scenery object types in the level map, drawn by the game's own
  routines (37302) from an in-game state; red = the walk-blocking boxes its box builder (60754)
  makes (where a figure's walk-test point, y + 6, cannot go). Some x >= 128 entries (crates 15/16/17,
  type 33) are pickup zones, drawn as bands.
- `scenery_types.png` - the 13 types seen in Dean's area-1 RZX, as drawn in play.
- `depth_options.png` - frames of the RZX rendered three ways: A figures in front (first build),
  B canopies in front, C depth-sorted. Dean chose the game's own box rule (nexclash
  games/commando.md).

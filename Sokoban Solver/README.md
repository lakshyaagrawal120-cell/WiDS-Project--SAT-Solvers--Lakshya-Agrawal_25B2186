# Sokoban Solver (SAT)

This is a Python program that solves **Sokoban** levels. Instead of writing a pathfinding algorithm like A*, I mapped the game rules into a boolean formula and used a SAT solver (`PySAT`) to find the solution.


### 1. Variables

I used three types of variables for every time step :

* **Player vars:** `Player(r, c, t)` 
* **Box vars:** `Box(r, c, t)` 
* **Action vars:** `Action(t, i)` 

### 2. The Logic

I wrote loops to add clauses (rules) to the formula.

* **Basics:** The player can't be in a wall, and you can only take one action at a time.
* **Movement:** If the player takes action **UP**, and the spot above is empty, the player moves there at .
* **Pushing:** If the player moves **UP** into a box, and the spot behind the box is empty, both the player and the box move up.

### 3. The Frame Problem

The hardest part was telling the solver what doesn't change.
In my first few tries, boxes kept disappearing or duplicating because I didn't explicitly tell the solver they had to stay put if I wasn't touching them.

**My Solution:**

Inside the transition loop, I check the chosen action (e.g., UP).

* If we are moving **UP**, only the specific cells involved in that move (the player's spot and the box's spot) are allowed to change.
* For **every other cell** on the board, I added a rule: `Box_at_t <-> Box_at_t+1`.
This strictly forces everything else to freeze, which stopped the teleporting bugs.

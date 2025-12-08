import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # even if unused, required for 3D plotting
import matplotlib.animation as animation

# ---------------------------
# Projection from 4D to 3D
# ---------------------------
def project_point(point, d=3.0):
    """
    Perspective projection from 4D to 3D.
    The 4D point is (x, y, z, w). We project by treating w as the “depth”.
    Points with larger w are closer to the viewer.
    
    Projection:
        (x, y, z, w) --> (x/(d-w), y/(d-w), z/(d-w))
    
    d should be chosen so that d - w != 0. Since our tesseract lives in [-1,1],
    d=3 is a safe choice.
    """
    x, y, z, w = point
    factor = d - w
    return np.array([x, y, z]) / factor

# ---------------------------
# Build the Tesseract Wireframe
# ---------------------------
def get_tesseract_edges():
    """
    Generate the vertices and edges for a tesseract.
    Vertices: All 16 points with coordinates ±1.
    An edge exists between vertices that differ in exactly one coordinate.
    """
    vertices = []
    # There are 16 vertices in a 4D hypercube: each coordinate is either -1 or 1.
    for i in range(16):
        # Generate each coordinate from bits of i.
        coords = [1 if (i >> j) & 1 else -1 for j in range(4)]
        vertices.append(np.array(coords, dtype=float))
    vertices = np.array(vertices)
    
    edges = []
    # Two vertices are connected by an edge if they differ in exactly one coordinate.
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            # Count in how many coordinates they differ by 2 (since 1 - (-1) = 2)
            if np.sum(np.abs(vertices[i] - vertices[j]) == 2) == 1:
                edges.append((i, j))
    return vertices, edges

# Precompute tesseract vertices and edges.
tesseract_vertices, tesseract_edges = get_tesseract_edges()

# Project all vertices for drawing the wireframe.
def project_tesseract(d=3.0):
    proj_vertices = np.array([project_point(v, d=d) for v in tesseract_vertices])
    return proj_vertices

# ---------------------------
# Simulation Parameters
# ---------------------------
# Time step
dt = 0.01

# Tesseract boundaries (in 4D, each coordinate between -1 and 1)
BOUND_MIN = -1.0
BOUND_MAX = 1.0

# Initial state for the ball in 4D.
# Position: randomly inside the tesseract.
pos = np.random.uniform(BOUND_MIN, BOUND_MAX, size=4)
# Velocity: random direction with moderate speed.
vel = np.random.uniform(-1, 1, size=4)

# ---------------------------
# Ball Update Function
# ---------------------------
def update_ball(pos, vel, dt):
    """
    Update the 4D position of the ball with elastic bouncing.
    For each coordinate, if the new position would lie outside the boundary,
    reflect the coordinate and reverse that component of the velocity.
    """
    new_pos = pos + vel * dt

    # Check boundaries and reflect if needed.
    for i in range(4):
        if new_pos[i] > BOUND_MAX:
            # Reflect from the boundary:
            new_pos[i] = BOUND_MAX - (new_pos[i] - BOUND_MAX)
            vel[i] = -vel[i]
        elif new_pos[i] < BOUND_MIN:
            new_pos[i] = BOUND_MIN + (BOUND_MIN - new_pos[i])
            vel[i] = -vel[i]
    return new_pos, vel

# ---------------------------
# Set Up the Figure
# ---------------------------
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Set axis limits for a better view.
ax.set_xlim(-3, 3)
ax.set_ylim(-3, 3)
ax.set_zlim(-3, 3)
ax.set_title("Ball Bouncing inside a Tesseract (4D projected to 3D)")
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")

# Draw the tesseract wireframe.
proj_vertices = project_tesseract(d=3.0)
for i, j in tesseract_edges:
    pts = np.vstack((proj_vertices[i], proj_vertices[j]))
    ax.plot(pts[:,0], pts[:,1], pts[:,2], color='gray', linewidth=0.5)

# Draw the ball as a scatter point.
ball_point, = ax.plot([], [], [], 'o', color='red', markersize=8)

# ---------------------------
# Animation Function
# ---------------------------
def animate(frame):
    global pos, vel
    # Update the ball's 4D position.
    pos, vel = update_ball(pos, vel, dt)
    # Project the ball's 4D position into 3D.
    proj_ball = project_point(pos, d=3.0)
    
    # Update the scatter plot.
    ball_point.set_data(proj_ball[0:2])
    ball_point.set_3d_properties(proj_ball[2])
    return ball_point,

# Create the animation.
ani = animation.FuncAnimation(fig, animate, frames=1000, interval=10, blit=True)

plt.show()
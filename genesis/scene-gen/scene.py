import argparse
import genesis as gs
from time import time
import numpy as np
import sys
import select

def random_rotation():
    """Generate random Euler angles for initial rotation."""
    return (np.random.uniform(0, 360), np.random.uniform(0, 360), np.random.uniform(0, 360))


def euler_to_quat(euler):
    """Convert Euler angles (degrees) to quaternion [w, x, y, z]."""
    # Convert to radians
    roll, pitch, yaw = np.radians(euler)

    # Convert to quaternion
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return np.array([w, x, y, z])


def random_position(x_range=(-3, 3), y_range=(-3, 3), z_range=(3, 7)):
    """Generate random position within specified ranges."""
    return (
        np.random.uniform(*x_range),
        np.random.uniform(*y_range),
        np.random.uniform(*z_range)
    )


obj_files = {
    "gear": {
        "path": "parts/100T_gear - 615234/100T_gear - 615234.obj"
    },
    "bottom_arm": {
        "path": "parts/bottom_arm_2 - Part 1/bottom_arm_2 - Part 1.obj"
    },
    "motor_assembly": {
        "path": "parts/motor_assembly/motor_assembly.obj"
    },
    "base_plate": {
        "path": "parts/base_plate - Part 1/base_plate - Part 1.obj"
    },
    "motor_mount": {
        "path": "parts/motor_mount - Part 1/motor_mount - Part 1.obj"
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="warning")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(5, 5, 3),
            camera_lookat=(0, 0, 1.5),
            camera_up=(0, 0, 1),
            camera_fov=60,
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0, 0, -9.8),
        ),
    )

    ########################## entities ##########################
    # Add ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Add rigid objects from obj_files with random positions and rotations
    gear = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["gear"]["path"],
            scale=20.0,
            pos=random_position(),
            euler=random_rotation(),
        ),
    )

    bottom_arm = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["bottom_arm"]["path"],
            scale=20.0,
            pos=random_position(),
            euler=random_rotation(),
        ),
    )

    motor_assembly = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["motor_assembly"]["path"],
            scale=20.0,
            pos=random_position(),
            euler=random_rotation(),
        ),
    )

    base_plate = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["base_plate"]["path"],
            scale=20.0,
            pos=random_position(),
            euler=random_rotation(),
        ),
    )

    motor_mount = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["motor_mount"]["path"],
            scale=20.0,
            pos=random_position(),
            euler=random_rotation(),
        ),
    )

    ########################## build ##########################
    scene.build()

    run_sim(scene, args.vis)


def run_sim(scene, enable_vis):
    print("\n=== Simulation Running ===")
    print("Genesis viewer shortcuts:")
    print("  [i] = hide/show shortcuts")
    print("  [r] = record video")
    print("  [s] = save image")
    print("  [z] = reset camera")
    print("  [F11] = fullscreen")
    print("\nInteractive controls (type in terminal):")
    print("  Type 'reset' + Enter to reset simulation with new random config")
    print("  Type 'quit' + Enter to exit")
    print("==========================\n")

    # Store references to entities (assuming they're indexed 1-5, after the ground plane at 0)
    entities = list(range(1, 6))  # gear, bottom_arm, motor_assembly, base_plate, motor_mount

    t_prev = time()
    i = 0

    while True:
        # Check for terminal input (non-blocking)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip().lower()
            if line == 'reset':
                print("\n🔄 Resetting simulation with new random positions and rotations...")
                scene.reset()

                # Set new random positions and rotations for each entity
                for entity_idx in entities:
                    new_pos = random_position()
                    new_quat = euler_to_quat(random_rotation())
                    # qpos is [x, y, z, qw, qx, qy, qz] - 7 values total
                    scene.entities[entity_idx].set_qpos(np.concatenate([new_pos, new_quat]))

                i = 0
                print("✓ Reset complete with new random config!\n")
            elif line == 'quit':
                print("Exiting simulation...")
                break

        # Auto-reset every 500 steps
        if i > 0 and i % 500 == 0:
            print("\n🔄 Auto-reset at step 500...")
            scene.reset()

            # Set new random positions and rotations for each entity
            for entity_idx in entities:
                new_pos = random_position()
                new_quat = euler_to_quat(random_rotation())
                scene.entities[entity_idx].set_qpos(np.concatenate([new_pos, new_quat]))

            i = 0
            print("✓ Reset complete with new random config!\n")

        scene.step()

        # Check if viewer is still active
        if enable_vis and not scene.viewer.is_alive():
            break

        t_now = time()
        if i % 300 == 0:  # Print less frequently
            print(f"Step {i}, FPS: {1 / (t_now - t_prev):.1f} | Type 'reset' or 'quit' and press Enter")
        t_prev = t_now
        i += 1


if __name__ == "__main__":
    main()

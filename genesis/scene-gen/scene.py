import argparse
import genesis as gs
from time import time

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
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="debug")

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

    # Add rigid objects from obj_files, spaced apart to avoid initial intersection
    gear = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["gear"]["path"],
            scale=20.0,
            pos=(0, 0, 2.0),
        ),
    )

    bottom_arm = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["bottom_arm"]["path"],
            scale=20.0,
            pos=(1.5, 0, 2.5),
        ),
    )

    motor_assembly = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["motor_assembly"]["path"],
            scale=20.0,
            pos=(-1.5, 0, 3.0),
        ),
    )

    base_plate = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["base_plate"]["path"],
            scale=20.0,
            pos=(0, 1.5, 3.5),
        ),
    )

    motor_mount = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["motor_mount"]["path"],
            scale=20.0,
            pos=(0, -1.5, 4.0),
        ),
    )

    ########################## build ##########################
    scene.build()

    run_sim(scene, args.vis)


def run_sim(scene, enable_vis):
    horizon = 2000
    t_prev = time()

    for i in range(horizon):
        scene.step()
        t_now = time()
        if i % 10 == 0:
            print(f"Step {i}, FPS: {1 / (t_now - t_prev):.1f}")
        t_prev = t_now


if __name__ == "__main__":
    main()

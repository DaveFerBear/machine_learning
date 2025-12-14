import argparse
import numpy as np
import genesis as gs
from time import time


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
            substeps=10,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, 3, 2.5),
            camera_lookat=(0, 0, 1.0),
            camera_up=(0, 0, 1),
            camera_fov=50,
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0, 0, -9.8),
        ),
    )

    ########################## materials ##########################
    mat_elastic = gs.materials.PBD.Elastic()

    ########################## entities ##########################

    # Add ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Rigid bunnies
    bunny = scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/bunny.obj",
            scale=0.5,
            pos=(0, 0, 2.0),
        ),
    )

    bunny2 = scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/bunny.obj",
            scale=0.4,
            pos=(-0.2, -0.2, 3.5),
        ),
    )

    # Elastic dragon (soft body)
    dragon = scene.add_entity(
        material=mat_elastic,
        morph=gs.morphs.Mesh(
            file="meshes/dragon/dragon.obj",
            scale=0.003,
            pos=(0.3, 0.2, 2.5),
        ),
        surface=gs.surfaces.Default(),
    )
    ########################## build ##########################
    scene.build()

    run_sim(scene, args.vis)


def run_sim(scene, enable_vis):
    horizon = 2000  # Longer simulation to see them settle
    t_prev = time()

    for i in range(horizon):
        scene.step()
        t_now = time()
        if i % 10 == 0:  # Print FPS every 10 steps to reduce spam
            print(f"Step {i}, FPS: {1 / (t_now - t_prev):.1f}")
        t_prev = t_now


if __name__ == "__main__":
    main()
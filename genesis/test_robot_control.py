import argparse

import torch
import numpy as np
import genesis as gs


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 1.2, 0.8),
            camera_fov=50,
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0.0, 0.0, -10.0),
        ),
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())
    franka = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    ########################## build ##########################
    scene.build()

    ############ Optional: set control gains ############
    jnt_names = [
        'joint1',
        'joint2',
        'joint3',
        'joint4',
        'joint5',
        'joint6',
        'joint7',
        'finger_joint1',
        'finger_joint2',
    ]
    dofs_idx = [franka.get_joint(name).dof_idx_local for name in jnt_names]

    # set positional gains
    franka.set_dofs_kp(
        kp             = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
        dofs_idx_local = dofs_idx,
    )
    # set velocity gains
    franka.set_dofs_kv(
        kv             = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
        dofs_idx_local = dofs_idx,
    )
    # set force range for safety
    franka.set_dofs_force_range(
        lower          = np.array([-87, -87, -87, -87, -12, -12, -12, -100, -100]),
        upper          = np.array([ 87,  87,  87,  87,  12,  12,  12,  100,  100]),
        dofs_idx_local = dofs_idx,
    )

    run_sim(scene, franka, dofs_idx, args.vis)


def run_sim(scene, franka, dofs_idx, enable_vis):
    from time import time

    t_prev = time()
    i = 0
    while True:
        i += 1

        if i == 0:
            franka.control_dofs_position(
                np.array([1, 1, 0, 0, 0, 0, 0, 0.04, 0.04]),
                dofs_idx,
            )
        elif i == 250:
            franka.control_dofs_position(
                np.array([-1, 0.8, 1, -2, 1, 0.5, -0.5, 0.04, 0.04]),
                dofs_idx,
            )
        elif i == 500:
            franka.control_dofs_position(
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
                dofs_idx,
            )
        elif i == 750:
            # control first dof with velocity, and the rest with position
            franka.control_dofs_position(
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])[1:],
                dofs_idx[1:],
            )
            franka.control_dofs_velocity(
                np.array([1.0, 0, 0, 0, 0, 0, 0, 0, 0])[:1],
                dofs_idx[:1],
            )
        elif i == 1000:
            franka.control_dofs_force(
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]),
                dofs_idx,
            )
        # This is the control force computed based on the given control command
        # If using force control, it's the same as the given control command
        print('control force:', franka.get_dofs_control_force(dofs_idx))

        # This is the actual force experienced by the dof
        print('internal force:', franka.get_dofs_force(dofs_idx))

    

        scene.step()

        t_now = time()
        print(1 / (t_now - t_prev), "FPS")
        t_prev = t_now
        if i > 1250:
            break

    # if enable_vis:
    #     scene.viewer.stop()


if __name__ == "__main__":
    main()
import argparse
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
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=30,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )
    franka = scene.add_entity(
        gs.morphs.MJCF(
            file="xml/franka_emika_panda/panda.xml",
            pos=(1.0, 1.0, 0.0),
            euler=(0, 0, 0),
        ),
    )
    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.04, 0.04, 0.04),
            pos=(0.65, 0.0, 0.02),
        ),
    )

    ########################## build ##########################
    scene.build()

    jnt_names = [
        'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6', 'joint7',
        'finger_joint1', 'finger_joint2',
    ]
    dofs_idx = [franka.get_joint(name).dof_idx_local for name in jnt_names]

    # Positional gains
    franka.set_dofs_kp(
        kp = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
        dofs_idx_local = dofs_idx,
    )

    # Velocity gains
    franka.set_dofs_kv(
        kv = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
        dofs_idx_local = dofs_idx,
    )

    # Force safety limits
    franka.set_dofs_force_range(
        lower = np.array([-87, -87, -87, -87, -12, -12, -12, -100, -100]),
        upper = np.array([87, 87, 87, 87, 12, 12, 12, 100, 100]),
        dofs_idx_local = dofs_idx,
    )

    run_sim(scene, franka, cube, dofs_idx, args.vis)


def run_sim(scene, franka, cube, dofs_idx, enable_vis):
    rigid = scene.sim.rigid_solver
    end_effector = franka.get_link("hand")
    cube_link = cube.get_link("box_baselink")

    # Pre-grasp positioning
    q_pregrasp = franka.inverse_kinematics(
        link = end_effector,
        pos = np.array([0.65, 0.0, 0.13]),
        quat = np.array([0, 1, 0, 0]),
    )
    franka.control_dofs_position(q_pregrasp[:-2], np.arange(7))
    for _ in range(50):
        scene.step()

    # Attach (activate suction)
    link_cube = np.array([cube_link.idx], dtype=gs.np_int)
    link_franka = np.array([end_effector.idx], dtype=gs.np_int)
    rigid.add_weld_constraint(link_cube, link_franka)

    # Lift and transport
    q_lift = franka.inverse_kinematics(
        link = end_effector,
        pos = np.array([0.65, 0.0, 0.28]),
        quat = np.array([0, 1, 0, 0]),
    )
    franka.control_dofs_position(q_lift[:-2], np.arange(7))
    for _ in range(50):
        scene.step()

    q_place = franka.inverse_kinematics(
        link = end_effector,
        pos = np.array([0.4, 0.2, 0.18]),
        quat = np.array([0, 1, 0, 0]),
    )
    franka.control_dofs_position(q_place[:-2], np.arange(7))
    for _ in range(100):
        scene.step()

    # Detach (release suction)
    rigid.delete_weld_constraint(link_cube, link_franka)
    for _ in range(400):
        scene.step()


if __name__ == "__main__":
    main()
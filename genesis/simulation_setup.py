import numpy as np
import genesis as gs


def setup_scene(show_viewer: bool = False):
    """
    Set up the Genesis scene with robot arm, R3 frame, and environment.

    Args:
        show_viewer: Whether to display the visualization window

    Returns:
        tuple: (scene, arm, dofs_idx, end_effector, stream_camera)
    """
    # Initialize Genesis
    gs.init(backend=gs.gpu, logging_level="warning")

    # Create scene
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
        vis_options=gs.options.VisOptions(
            show_world_frame=True,
            world_frame_size=0.2,
            show_link_frame=False,
            show_cameras=False,
        ),
        show_viewer=show_viewer,
    )

    # Add plane
    plane = scene.add_entity(
        gs.morphs.Plane(),
        surface=gs.surfaces.Default(
            color=(0.8, 0.8, 0.8, 1.0),
        ),
    )

    # Add static R3 frame at origin
    r3_frame = scene.add_entity(
        morph=gs.morphs.Mesh(
            file="./scene-gen/parts/R3_frame/R3_frame.glb",
            scale=1.0,
            pos=(0.5, 0, 0.3),
            euler=(0, 0, 0),
            fixed=True,
        ),
        surface=gs.surfaces.Default(color=(0.05, 0.05, 0.05, 1.0)),
    )

    # Add 6-DOF arm
    arm = scene.add_entity(
        gs.morphs.MJCF(
            file="./robots/dummy-6dof.xml",
            pos=(0.5, 0.0, 0.55),
            euler=(0, 0, 90),
        ),
    )

    # Joint names and indices
    jnt_names = [
        "SHOULDER_A", "SHOULDER_B", "SHOULDER_C",
        "ELBOW_A", "ELBOW_B", "WRIST_A",
    ]
    dofs_idx = [arm.get_joint(name).dof_idx_local for name in jnt_names]

    # Add cube
    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.04, 0.04, 0.04),
            pos=(0.6, 0.0, 0.02),
        ),
    )

    # Add camera for streaming (positioned to view workspace)
    # Must be added BEFORE scene.build()
    stream_camera = scene.add_camera(
        res=(1280, 720),
        pos=(0, -2.5, 1.5),
        lookat=(0.5, 0.0, 0.5),
        fov=50,
        GUI=False,
    )

    # Build scene
    scene.build()

    # Get end effector link
    end_effector = arm.get_link("hand")

    # Configure PD gains
    arm.set_dofs_kp(
        kp=np.array([200.0, 200.0, 150.0, 120.0, 120.0, 50.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_kv(
        kv=np.array([20.0, 20.0, 15.0, 10.0, 10.0, 5.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_force_range(
        lower=np.array([-50.0, -50.0, -30.0, -30.0, -20.0, -10.0]),
        upper=np.array([50.0, 50.0, 30.0, 30.0, 20.0, 10.0]),
        dofs_idx_local=dofs_idx,
    )

    # Set initial joint position
    initial_joints = np.array([1.4604863, 0.7191452, -0.12146536, -0.41686273, 0.15724644, -0.98767394])
    arm.set_dofs_position(initial_joints, dofs_idx)

    # Let it settle
    for _ in range(50):
        scene.step()

    return scene, arm, dofs_idx, end_effector, stream_camera

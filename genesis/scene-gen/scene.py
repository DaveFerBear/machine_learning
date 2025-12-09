import argparse
import genesis as gs
from time import time
import numpy as np
import sys
import select
import os
import json
from datetime import datetime
from PIL import Image
from math_utils import random_position, random_rotation, euler_to_quat, get_entity_bbox


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
    "rpi_case_bottom": {
        "path": "parts/rpi_case_bottom/rpi_case_bottom.glb"
    },
    "bolt": {
        "path": "parts/bolt/bolt.glb"
    },
    "raspberry_pi_cooler": {
        "path": "parts/raspberry_pi_5_active_cooler/raspberry_pi_active_cooling.glb"
    },
    "fan": {
        "path": "parts/fan/fan.glb"
    },
    "active_cooler": {
        "path": "parts/active_cooler/active_cooler.glb"
    },
    "rpi_case_top": {
        "path": "parts/rpi_case_top/rpi_case_top.glb"
    },
    "raspberry_pi": {
        "path": "parts/raspberry_pi_5 - 00001/raspberry_pi.glb",
    },
    "R3_frame": {
        "path": "parts/R3_frame/R3_frame.glb"
    },
}

SCENE_ONE_PARTS = ["gear", "bottom_arm", "motor_assembly", "base_plate", "motor_mount"]
SCENE_TWO_PARTS = ["rpi_case_bottom", "raspberry_pi_cooler", "fan", "active_cooler", "rpi_case_top", "raspberry_pi"]
SCENE_THREE_PARTS = ["raspberry_pi", "fan", "active_cooler"]

_SCENE_PARTS = SCENE_THREE_PARTS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    parser.add_argument("-p", "--capture", action="store_true", default=False, help="Capture image on reset")
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu, logging_level="warning")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.001,
            substeps=20,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.5, 0.6, 0.6),
            camera_lookat=(0.5, 0.3, 0),
            camera_up=(0, 0, 1),
            camera_fov=75,
        ),
        vis_options = gs.options.VisOptions(
            show_world_frame = True,
            world_frame_size = 1.0, # length of the world frame in meter
            show_link_frame  = False,
            show_cameras     = False,
            plane_reflection = False,
            ambient_light    = (0.7, 0.7, 0.7),
        ),
        show_viewer=args.vis,
        rigid_options=gs.options.RigidOptions(
            dt=0.05,
            gravity=(0, 0, -9.8),
        ),
    )

    ########################## entities ##########################
    # Add ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Add static R3 frame at origin (fixed = not affected by physics)
    r3_frame = scene.add_entity(
        morph=gs.morphs.Mesh(
            file=obj_files["R3_frame"]["path"],
            scale=obj_files["R3_frame"].get("scale", 1.0),
            pos=(0.5, 0, 0.3),
            euler=(0, 0, 0),
            fixed=True,  # Makes it static/fixed
        ),
        surface=gs.surfaces.Default(color=(0.05, 0.05, 0.05, 1.0)),  # Black material
    )

    # Add rigid objects dynamically from _SCENE_PARTS
    for part_name in _SCENE_PARTS:
        scene.add_entity(
            morph=gs.morphs.Mesh(
                file=obj_files[part_name]["path"],
                scale=obj_files[part_name].get("scale", 1.0),
                pos=random_position(),
                euler=random_rotation(),
            ),
            surface=gs.surfaces.Default(color=(0.9, 0.9, 0.9, 1.0)),  # Grey material
        )

    ########################## add cameras ##########################
    # Create cameras at the 4 corners of the grid looking at center
    cameras = []

    # Define 4 camera positions at corners of 1m x 0.6m x 0.6m grid
    # Cameras at top corners looking down 45° inward at center floor point
    camera_positions = [
        {"pos": (0, 0, 0.6), "lookat": (0.3, 0.3, 0), "name": "corner1"},   # Corner (0,0,0.6)
        {"pos": (1, 0, 0.6), "lookat": (0.7, 0.3, 0), "name": "corner2"},   # Corner (1,0,0.6)
        {"pos": (0, 0.6, 0.6), "lookat": (0.3, 0.3, 0), "name": "corner3"}, # Corner (0,0.6,0.6)
        {"pos": (1, 0.6, 0.6), "lookat": (0.7, 0.3, 0), "name": "corner4"}, # Corner (1,0.6,0.6)
    ]

    CAMERA_PARAMS = {
        "fov": 60,
        "aperture": 3.8,
        "res": (1920, 1080),
    }

    for cam_pos in camera_positions:
        cam = scene.add_camera(
            pos=cam_pos["pos"],
            lookat=cam_pos["lookat"],
            **CAMERA_PARAMS,
        )
        cameras.append({
            "camera": cam,
            "pos_name": cam_pos["name"],
            **CAMERA_PARAMS,
        })

    ########################## build ##########################
    scene.build()

    run_sim(scene, args.vis, args.capture, cameras, camera_positions, CAMERA_PARAMS)


def check_collisions(scene, entities):
    """Check for rigid body collisions and print which objects are touching."""
    # Use the rigid solver's collision detection method
    collision_pairs = scene.rigid_solver.detect_collision()

    # Get mapping from geometry -> link -> entity
    geoms_info = scene.rigid_solver.geoms_info
    links_info = scene.rigid_solver.links_info

    # Convert to numpy for easier access
    geom_to_link = geoms_info.link_idx.to_numpy()
    link_to_entity = links_info.entity_idx.to_numpy()

    # Map collision pairs from geometry indices to entity indices
    entity_collisions = set()
    for geom_a, geom_b in collision_pairs:
        # Skip ground collisions (geom 0)
        if geom_a == 0 or geom_b == 0:
            continue

        # Map geom -> link -> entity
        link_a = geom_to_link[geom_a]
        link_b = geom_to_link[geom_b]
        entity_a = link_to_entity[link_a]
        entity_b = link_to_entity[link_b]

        # Only include our entities (R3_frame=1, parts=2+)
        if entity_a >= 1 and entity_b >= 1:
            # Store as sorted tuple to avoid duplicates
            entity_collisions.add(tuple(sorted([entity_a, entity_b])))

    if len(entity_collisions) > 0:
        print(f"\n🔴 Detected {len(entity_collisions)} collision(s):")

        # Print collision pairs
        for entity_a, entity_b in sorted(entity_collisions):
            name_a = get_entity_name_from_idx(entity_a)
            name_b = get_entity_name_from_idx(entity_b)

            print(f"  • {name_a} <-> {name_b}")
    else:
        print("\n✓ No collisions detected (between our parts)")


def get_entity_name_from_idx(entity_idx):
    """Map entity index to entity name."""
    # Entity indices: 0=ground, 1=R3_frame, 2+=parts
    if entity_idx == 0:
        return "ground"
    elif entity_idx == 1:
        return "R3_frame"
    elif entity_idx - 2 < len(_SCENE_PARTS):
        return _SCENE_PARTS[entity_idx - 2]
    else:
        return f"entity_{entity_idx}"


def run_sim(scene, enable_vis, capture_images, cameras, camera_positions, camera_params):
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

    # Create render session directory if capture mode is enabled
    render_session_dir = None
    if capture_images:
        session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        render_session_dir = os.path.join("renders", session_name)
        os.makedirs(render_session_dir, exist_ok=True)
        print(f"  📸 Capture mode: Images will be saved to {render_session_dir}/")

        # Generate scene_spec.json
        scene_spec = {
            "session_id": session_name,
            "date_generated": datetime.now().isoformat(),
            "parts": list(_SCENE_PARTS),
            "lighting": {
                "ambient_light": [0.7, 0.7, 0.7]
            },
            "cameras": [
                {
                    "id": cam_pos["name"],
                    "position": list(cam_pos["pos"]),
                    "lookat": list(cam_pos["lookat"]),
                    "fov": camera_params["fov"],
                    "aperture": camera_params["aperture"],
                    "resolution": list(camera_params["res"])
                }
                for cam_pos in camera_positions
            ]
        }

        scene_spec_path = os.path.join(render_session_dir, "scene_spec.json")
        with open(scene_spec_path, 'w') as f:
            json.dump(scene_spec, f, indent=2)
        print(f"  📄 Scene spec saved to {scene_spec_path}")

    print("==========================\n")

    # Store references to entities (after the ground plane at 0)
    # Entity indices: 0=ground, 1=R3_frame (static), 2+=dynamic parts
    entities = list(range(2, len(_SCENE_PARTS) + 2))

    # Path to scenes.jsonl file
    scenes_jsonl_path = None
    if capture_images and render_session_dir is not None:
        scenes_jsonl_path = os.path.join(render_session_dir, "scenes.jsonl")

    t_prev = time()
    i = 0
    reset_count = 0

    while True:
        # Check for terminal input (non-blocking)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip().lower()
            if line == 'reset':
                # Check collisions before reset
                check_collisions(scene, entities)

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

        # Auto-reset every 100 steps
        if i > 0 and i % 40 == 0:
            # Capture images from all 4 camera angles
            if capture_images and render_session_dir is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                iso_timestamp = datetime.now().isoformat()

                # Collect part information (positions, rotations, bounding boxes)
                parts_data = []
                for idx, entity_idx in enumerate(entities):
                    entity = scene.entities[entity_idx]
                    part_name = _SCENE_PARTS[idx]

                    # Get qpos: [x, y, z, qw, qx, qy, qz]
                    qpos = entity.get_qpos()
                    position = qpos[:3].tolist()
                    rotation_quat = qpos[3:].tolist()

                    # Get axis-aligned bounding box
                    bbox_min, bbox_max = get_entity_bbox(entity, position)

                    parts_data.append({
                        "name": part_name,
                        "position": position,
                        "rotation_quat": rotation_quat,
                        "bbox_min": bbox_min,
                        "bbox_max": bbox_max
                    })

                # Capture from all 4 corner cameras
                captures_data = []
                for corner_idx in range(4):
                    cam_config = cameras[corner_idx]
                    camera = cam_config["camera"]

                    render_result = camera.render()
                    rgb = render_result[0] if isinstance(render_result, tuple) else render_result
                    res_str = f"{cam_config['res'][0]}x{cam_config['res'][1]}"
                    fov_str = f"{cam_config['fov']}"
                    pos_name = cam_config['pos_name']
                    filename = f"scene_{reset_count:04d}_{timestamp}_{pos_name}_{res_str}_fov{fov_str}.png"
                    filepath = os.path.join(render_session_dir, filename)
                    img = Image.fromarray(rgb.astype(np.uint8))
                    img.save(filepath)
                    print(f"📸 Captured: {filename} (pos={pos_name}, res={res_str}, fov={fov_str}°)")

                    captures_data.append({
                        "camera_id": pos_name,
                        "filename": filename,
                        "camera_position": list(camera_positions[corner_idx]["pos"]),
                        "camera_lookat": list(camera_positions[corner_idx]["lookat"])
                    })

                # Write scene data to JSONL
                scene_data = {
                    "scene_id": reset_count,
                    "timestamp": iso_timestamp,
                    "parts": parts_data,
                    "captures": captures_data
                }

                with open(scenes_jsonl_path, 'a') as f:
                    f.write(json.dumps(scene_data) + '\n')
                print(f"📝 Scene data appended to scenes.jsonl")

                reset_count += 1

            # Check collisions before auto-reset
            check_collisions(scene, entities)

            print("\n🔄 Auto-reset at step 40...")
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

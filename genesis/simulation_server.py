import argparse
import threading
import cv2
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from simulation_setup import setup_scene
from simulation_api import SimulationController


# Request model for move endpoint
class MoveRequest(BaseModel):
    x: float
    y: float
    z: float


# Global controller instance
controller = None


# Create FastAPI app
app = FastAPI(title="Genesis Simulation Server")

# Add CORS middleware to allow requests from Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/move")
async def move(request: MoveRequest):
    """
    Queue a move command to the specified position.

    Args:
        request: MoveRequest with x, y, z coordinates

    Returns:
        Status information including queue length
    """
    result = controller.move(request.x, request.y, request.z)
    return result


@app.get("/status")
async def get_status():
    """
    Get current status of the simulation.

    Returns:
        Current task, queue length, and position information
    """
    return controller.get_status()


@app.get("/cameras")
async def get_cameras():
    """
    Get list of available cameras.

    Returns:
        List of camera IDs
    """
    camera_ids = [camera_id for camera_id, _ in controller.cameras]
    return {"cameras": camera_ids}


@app.get("/stream/{camera_id}")
async def video_stream(camera_id: str):
    """
    MJPEG video stream endpoint for a specific camera.
    Returns a continuous stream of JPEG frames from the specified camera.
    Can be viewed directly in a browser: <img src="http://localhost:8000/stream/camera-id">
    """
    def generate():
        while True:
            # Get latest frame from controller for this camera
            frame = controller.get_latest_frame(camera_id)

            if frame is None:
                # No frame available yet, skip
                continue

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
                                    [cv2.IMWRITE_JPEG_QUALITY, 80])

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/stream")
async def video_stream_default():
    """
    MJPEG video stream endpoint for the default (first) camera.
    Returns a continuous stream of JPEG frames from the first camera.
    Can be viewed directly in a browser: <img src="http://localhost:8000/stream">
    """
    def generate():
        while True:
            # Get latest frame from controller (default camera)
            frame = controller.get_latest_frame()

            if frame is None:
                # No frame available yet, skip
                continue

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
                                    [cv2.IMWRITE_JPEG_QUALITY, 80])

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Genesis Simulation Server",
        "endpoints": {
            "POST /move": "Queue a move command (body: {x, y, z})",
            "GET /status": "Get current simulation status",
            "GET /cameras": "Get list of available cameras",
            "GET /stream": "MJPEG video stream from default camera (1280x720 @ ~30 FPS)",
            "GET /stream/{camera_id}": "MJPEG video stream from specific camera",
        }
    }


def run_server(host: str, port: int):
    """Run the FastAPI server in a background thread."""
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    global controller

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Genesis Simulation HTTP Server")
    parser.add_argument("-v", "--vis", action="store_true", default=False,
                        help="Show visualization window")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to bind the server to (default: 8000)")
    args = parser.parse_args()

    # Initialize scene on main thread (required for visualization)
    print("Initializing Genesis scene...")
    setup_result = setup_scene(show_viewer=args.vis)
    print("Scene initialized successfully")

    # Create simulation controller (but don't start background thread)
    print("Creating simulation controller...")
    controller = SimulationController(
        scene=setup_result['scene'],
        arm=setup_result['arm'],
        dofs_idx=setup_result['dofs_idx'],
        end_effector=setup_result['end_effector'],
        cameras=setup_result['cameras']
    )
    print("Simulation controller created")

    # Start FastAPI server in background thread
    print(f"\nStarting HTTP server on {args.host}:{args.port} (background thread)")
    server_thread = threading.Thread(
        target=run_server,
        args=(args.host, args.port),
        daemon=True
    )
    server_thread.start()

    print(f"Visualization: {'Enabled' if args.vis else 'Disabled'}")
    print("\nAPI Endpoints:")
    print(f"  POST http://{args.host}:{args.port}/move")
    print(f"  GET  http://{args.host}:{args.port}/status")
    print(f"  GET  http://{args.host}:{args.port}/stream  (MJPEG video @ 1280x720)")
    print("\nExample commands:")
    print(f"  curl -X POST http://{args.host}:{args.port}/move -H 'Content-Type: application/json' -d '{{\"x\": 0.4, \"y\": 0.2, \"z\": 0.3}}'")
    print(f"  Open in browser: http://{args.host}:{args.port}/stream")
    print("\nPress Ctrl+C to stop the server")
    print("\nStarting simulation loop on main thread...\n")

    # Run simulation loop on main thread (required for visualization)
    controller.running = True
    try:
        controller.run_on_main_thread()
    except KeyboardInterrupt:
        print("\nShutting down...")
        controller.stop()


if __name__ == "__main__":
    main()

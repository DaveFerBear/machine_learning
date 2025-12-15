# Periscope

A simple React interface for viewing and controlling robots.

## Features

- Live MJPEG video stream
- Position control panel (X, Y, Z coordinates)
- Real-time status display
- Queue length monitoring

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:3000 in your browser

## Prerequisites

Make sure your robot control server is running on `http://localhost:8000` with the following endpoints:
- `GET /stream` - MJPEG video stream
- `POST /move` - Queue move commands
- `GET /status` - Get current status

## Usage

1. View the live camera feed in the main panel
2. Enter X, Y, Z coordinates in the control panel
3. Click "Move to Position" to queue a movement command
4. Monitor the current task and queue length in the status section

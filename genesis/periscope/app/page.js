'use client'

import { useState, useEffect } from 'react'

export default function Home() {
  const [x, setX] = useState('0.4')
  const [y, setY] = useState('0.2')
  const [z, setZ] = useState('0.3')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [cameras, setCameras] = useState([])

  const API_URL = 'http://localhost:8000'

  // Fetch camera list on mount
  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await fetch(`${API_URL}/cameras`)
        const data = await response.json()
        setCameras(data.cameras || [])
      } catch (error) {
        console.error('Failed to fetch cameras:', error)
      }
    }

    fetchCameras()
  }, [])

  // Fetch status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/status`)
        const data = await response.json()
        setStatus(data)
      } catch (error) {
        console.error('Failed to fetch status:', error)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleMove = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          x: parseFloat(x),
          y: parseFloat(y),
          z: parseFloat(z),
        }),
      })

      const data = await response.json()
      console.log('Move queued:', data)
    } catch (error) {
      console.error('Failed to queue move:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Periscope</h1>

      <div className="layout">
        <div className="streams-section">
          {cameras.length === 0 ? (
            <div className="stream-container">
              <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
                Loading cameras...
              </div>
            </div>
          ) : (
            <div className="camera-grid">
              {cameras.map((cameraId) => (
                <div key={cameraId} className="camera-item">
                  <div className="camera-label">{cameraId}</div>
                  <div className="stream-container">
                    <img
                      src={`${API_URL}/stream/${cameraId}`}
                      alt={`${cameraId} feed`}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="control-panel">
          <h2>Control Panel</h2>

          <form onSubmit={handleMove}>
            <div className="input-group">
              <label htmlFor="x">X Position</label>
              <input
                id="x"
                type="number"
                step="0.01"
                value={x}
                onChange={(e) => setX(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label htmlFor="y">Y Position</label>
              <input
                id="y"
                type="number"
                step="0.01"
                value={y}
                onChange={(e) => setY(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label htmlFor="z">Z Position</label>
              <input
                id="z"
                type="number"
                step="0.01"
                value={z}
                onChange={(e) => setZ(e.target.value)}
              />
            </div>

            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Queueing...' : 'Move to Position'}
            </button>
          </form>

          {status && (
            <div className="status">
              <h3>Status</h3>
              <div className="status-item">
                <span className="status-label">Current Task:</span>
                <span className="status-value">{status.current_task}</span>
              </div>
              <div className="status-item">
                <span className="status-label">Queue Length:</span>
                <span className="status-value">{status.queue_length}</span>
              </div>
              {status.current_position && (
                <div className="status-item">
                  <span className="status-label">Position:</span>
                  <span className="status-value">
                    ({status.current_position.map(v => v.toFixed(2)).join(', ')})
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

import './globals.css'

export const metadata = {
  title: 'Periscope',
  description: 'Robot control interface',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

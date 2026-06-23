/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          dark: '#0B132B',       // Deep Navy
          slate: '#1C2541',      // Medium Dark Blue
          blue: '#3A506B',       // Muted Steel Blue
          light: '#5BC0BE',      // Pale Teal
          accent: '#E63946',     // Crimson Alert Accent
          hover: '#1D2A44',
          gray: '#F4F6F9',       // Light BG
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
        malayalam: ['Noto Sans Malayalam', 'sans-serif'],
      },
      boxShadow: {
        'premium': '0 4px 20px -2px rgba(11, 19, 43, 0.12), 0 2px 8px -1px rgba(11, 19, 43, 0.06)',
        'glass': '0 8px 32px 0 rgba(11, 19, 43, 0.08)',
      }
    },
  },
  plugins: [],
}

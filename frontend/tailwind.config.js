/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        academic: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc7fb',
          400: '#36abf7',
          500: '#0c8fe9',
          600: '#0270c7',
          700: '#0359a1',
          800: '#074b85',
          900: '#0c3f6e',
          950: '#082849',
        },
        faculty: {
          DEFAULT: '#7c3aed',
          dark: '#5b21b6',
          light: '#f5f3ff'
        },
        student: {
          DEFAULT: '#0284c7',
          dark: '#0369a1',
          light: '#f0f9ff'
        }
      }
    },
  },
  plugins: [],
}


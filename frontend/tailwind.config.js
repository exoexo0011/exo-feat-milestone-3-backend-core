/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // EXO brand palette – used across chat UI and settings.
        surface: {
          DEFAULT: '#ffffff',
          dark: '#0f1117',
        },
        panel: {
          DEFAULT: '#f5f6f8',
          dark: '#171a21',
        },
        accent: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
        },
      },
    },
  },
  plugins: [],
};

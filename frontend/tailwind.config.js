/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./App.{js,jsx,ts,tsx}', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        jarvis: {
          app: '#070A12',
          depth: '#0B1020',
          surface: '#111827',
          raised: '#182235',
          border: '#243047',
          cyan: '#38BDF8',
          cyanDeep: '#0284C7',
          violet: '#8B5CF6',
          success: '#22C55E',
          warning: '#F59E0B',
          error: '#F87171',
        },
      },
    },
  },
  plugins: [],
};

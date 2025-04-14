/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./static/css/**/*.css"
  ],
  theme: {
    extend: {
      colors: {
        'Color-Palette-Dark-BG': '#0D0F11',
        'Color-Palette-Dark-Unit-BG': '#191D23',
        'Color-Palette-Dark-Unit-BG-2': '#262C36',
        'Color-Palette-Dark-Unit-BG-Hover': '#2E3A45',
        'Color-Palette-Dark-Dash': '#334E68',
        'Color-Palette-Dark-Stroke': '#576776',
        'Color-Palette-Dark-Purpure': '#7B57E0',
        'Color-Palette-Dark-White': '#FFFFFF',
        'Typography-Dark-Base-Primary-Gray-1': '#E3E3E3',
        'Typography-Dark-Base-Secondary-Gray-2': '#B8C0CC',
        'Typography-Dark-Highlight-Primary': '#7B57E0',
        'Typography-Light-Base-Primary': '#2B2E48',
        'Typography-Dark-Success': '#2AA31F',
        'Typography-Dark-Error': '#F53B30',

      },
      screens: {
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px'
      },
      fontFamily:{
        'audiowide': ['Audiowide', 'sans-serif'],
        'pingfang': ['PingFang SC', 'system-ui', 'sans-serif']
      },
      fontSize: {
        '14':'0.875rem',
        '16':'1rem',
        '18':'1.125rem',
        '20':'1.25rem',
        '22':'1.375rem',
        '24':'1.5rem',
        '32':'2rem',
      },



    },
  },
  plugins: [
    require('tailwind-scrollbar'),
  ],
}


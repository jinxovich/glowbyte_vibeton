/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#1d3557",
        accent: "#ff6b35",
      },
    },
  },
  plugins: [],
};


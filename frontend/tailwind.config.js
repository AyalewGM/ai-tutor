/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        dashboard: "0 10px 30px rgba(15, 23, 42, 0.06)",
      },
    },
  },
  corePlugins: { preflight: false },
  plugins: [],
};

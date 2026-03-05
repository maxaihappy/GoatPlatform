import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        goat: {
          orange: "#f59e0b",
          dark: "#0a0a0b",
          card: "#18181b",
        },
      },
    },
  },
  plugins: [],
};
export default config;

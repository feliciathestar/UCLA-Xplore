/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        'ucla-blue': {
          DEFAULT: '#5BC2E7',
          50: '#EFF9FD',
          100: '#DCF2FA',
          200: '#B8E4F5',
          300: '#93D6F0',
          400: '#6FCEEB',
          500: '#5BC2E7', // Base color
          600: '#28B0E0',
          700: '#1A8DB5',
          800: '#136A89',
          900: '#0C475C',
        },
        'ucla-yellow': {
          DEFAULT: '#FFE14C',
          50: '#FFFBEB',
          100: '#FFF7D6',
          200: '#FFEFAD',
          300: '#FFE885',
          400: '#FFE14C', // Base color
          500: '#FFD700',
          600: '#CCAC00',
          700: '#998100',
          800: '#665600',
          900: '#332B00',
        },
        // Add these standard UI colors
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  // Make sure HSL variables are safe-listed for opacity variants
  safelist: [
    { pattern: /bg-(ucla-blue|ucla-yellow)/ },
    { pattern: /text-(ucla-blue|ucla-yellow)/ },
    { pattern: /border-(ucla-blue|ucla-yellow)/ },
  ],
}


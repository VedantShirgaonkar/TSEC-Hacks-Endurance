/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                bg: {
                    primary: '#212121',
                    secondary: '#0d0d0d',
                    hover: '#2f2f2f',
                },
                accent: {
                    primary: '#10a37f', // ChatGPT Green
                    secondary: '#6366f1', // Indigo
                },
                text: {
                    primary: '#ececf1',
                    secondary: '#c5c5d2',
                    tertiary: '#8e8ea0',
                },
                border: {
                    subtle: '#424242',
                }
            },
            fontFamily: {
                sans: ['Söhne', 'Segoe UI', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}

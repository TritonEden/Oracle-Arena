import type { Metadata } from "next";
import "./globals.css";
import Navbar from "../components/navbar/navbar";

export const metadata: Metadata = {
  title: "Oracle Arena",
  description: "NBA Stats and Predictions",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const darkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;
                const link = document.createElement("link");
                link.rel = "icon";
                link.href = darkMode ? "/images/logo.png" : "/images/darkLogo.png";
                document.head.appendChild(link);
              })();
            `,
          }}
        />
      </head>
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}

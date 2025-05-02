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
        {/* Dark mode favicon */}
        <link
          rel="icon"
          href="/images/logo.png"
          media="(prefers-color-scheme: dark)"
        />
        {/* Light mode favicon */}
        <link
          rel="icon"
          href="/images/logoBlack.png"
          media="(prefers-color-scheme: light)"
        />
      </head>
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}

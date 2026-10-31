import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

const display = Space_Grotesk({ variable: "--font-display", subsets: ["latin"] });
const code = JetBrains_Mono({ variable: "--font-code", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Second Brain", template: "%s · Second Brain" },
  description:
    "Your own AI agent. It learns how you think, remembers what you read, and acts for you.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${code.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}

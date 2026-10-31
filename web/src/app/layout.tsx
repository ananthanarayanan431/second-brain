import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Newsreader } from "next/font/google";
import "./globals.css";

const display = Inter({ variable: "--font-display", subsets: ["latin"] });
const heading = Newsreader({ variable: "--font-heading", subsets: ["latin"] });
const code = JetBrains_Mono({ variable: "--font-code", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Neramind", template: "%s · Neramind" },
  description:
    "Neramind is a mind for your time: your own AI agent that learns how your days go, remembers what you read, and suggests the right thing at the right moment.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${heading.variable} ${code.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">{children}</body>
    </html>
  );
}

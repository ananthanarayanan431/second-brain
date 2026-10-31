import { AgentToAgent } from "@/components/home/AgentToAgent";
import { Capabilities } from "@/components/home/Capabilities";
import { FinalCta, Footer } from "@/components/home/Closing";
import { DayBalance } from "@/components/home/DayBalance";
import { Hero } from "@/components/home/Hero";
import { Nav } from "@/components/home/Nav";
import { Principles } from "@/components/home/Principles";
import { VoiceAgent } from "@/components/home/VoiceAgent";

export default function HomePage() {
  return (
    <>
      <Nav />
      <main id="main" className="flex-1">
        <Hero />
        <Principles />
        <VoiceAgent />
        <Capabilities />
        <DayBalance />
        <AgentToAgent />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}

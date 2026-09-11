import { Header } from "@/components/header";
import { Hero } from "@/components/hero";
import { Features } from "@/components/features";
import { LiveDemoTeaser } from "@/components/live-demo-teaser";
import { AlertsShowcase } from "@/components/alerts-showcase";
import { ClimateStrip } from "@/components/climate-strip";
import { HowItWorks } from "@/components/how-it-works";
import { MoesStrip } from "@/components/moes-strip";
import { Faq } from "@/components/faq";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <>
      <Header />
      <main id="main-content">
        <Hero />
        <Features />
        <LiveDemoTeaser />
        <AlertsShowcase />
        <ClimateStrip />
        <HowItWorks />
        <MoesStrip />
        <Faq />
      </main>
      <Footer />
    </>
  );
}

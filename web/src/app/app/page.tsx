import type { Metadata } from "next";
import { AppWorkspace } from "@/components/app/AppWorkspace";

export const metadata: Metadata = { title: "App" };

export default function AppPage() {
  return <AppWorkspace />;
}

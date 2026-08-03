import { redirect } from "next/navigation"
import { auth } from "@/auth"
import LineShell from "@/components/line/line-shell"

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await auth()

  if (!session?.user) {
    redirect("/sign-in")
  }

  return <LineShell>{children}</LineShell>
}

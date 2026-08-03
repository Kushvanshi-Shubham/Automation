import { redirect } from "next/navigation"
import { auth } from "@/auth"

export const metadata = { title: "Desk" }

export default async function DeskLayout({ children }: { children: React.ReactNode }) {
  const session = await auth()
  if (!session?.user) redirect("/")
  return <>{children}</>
}

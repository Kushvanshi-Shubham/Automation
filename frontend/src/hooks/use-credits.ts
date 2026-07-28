"use client"

import { useQuery } from "@tanstack/react-query"
import { useSession } from "next-auth/react"
import { fetchApi } from "@/lib/api-client"

export function useCredits() {
  const { status } = useSession()

  const { data, isLoading, error } = useQuery({
    queryKey: ["credits"],
    queryFn: () => fetchApi("/billing/credits"),
    staleTime: 60000,
    enabled: status === "authenticated",
  })

  return {
    credits: data?.balance ?? 0,
    plan: data?.plan ?? "free",
    isLoading,
    error,
  }
}

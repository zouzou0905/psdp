import { notFound } from "next/navigation";
import { RoleWorkspace } from "@/components/workspace/role-workspace";
import { isModule } from "@/config/access-control";

export default async function WorkspaceRoute({ params }: { params: Promise<{ role: string; segments?: string[] }> }) {
  const { role, segments = [] } = await params;
  if (!isModule(role)) notFound();
  return <RoleWorkspace module={role} pathname={`/${role}${segments.length ? `/${segments.join("/")}` : ""}`} />;
}

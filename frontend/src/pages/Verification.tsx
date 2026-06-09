import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, PendingProvider, VerificationRequest } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const ROLE_LABELS: Record<string, string> = {
  administration: "Администрация",
  social_service: "Соцслужбы",
  moderator: "Модератор",
  resident: "Житель (организация)",
};

function isOrganization(r: VerificationRequest): boolean {
  return (r.verification_note || "").includes("[ОРГАНИЗАЦИЯ]");
}

export function Verification() {
  const [requests, setRequests] = useState<VerificationRequest[]>([]);
  const [providers, setProviders] = useState<PendingProvider[]>([]);
  const [loading, setLoading] = useState<number | null>(null);
  const [rejectNote, setRejectNote] = useState("");

  const load = () => {
    api.getPendingVerifications().then(setRequests).catch(console.error);
    api.getPendingProviders().then(setProviders).catch(console.error);
  };
  useEffect(() => { load(); }, []);

  const organizations = requests.filter(isOrganization);
  const officials = requests.filter((r) => !isOrganization(r));

  const handleUser = async (id: number, action: "approve" | "reject") => {
    setLoading(id);
    try {
      if (action === "approve") await api.approveVerification(id);
      else await api.rejectVerification(id, rejectNote || "Не подтверждены данные");
      setRejectNote("");
      load();
    } finally {
      setLoading(null);
    }
  };

  const handleProvider = async (id: number, action: "approve" | "reject") => {
    setLoading(id);
    try {
      if (action === "approve") await api.approveProvider(id);
      else await api.rejectProvider(id, rejectNote || "Не подтверждены данные");
      setRejectNote("");
      load();
    } finally {
      setLoading(null);
    }
  };

  const renderUserCard = (r: VerificationRequest) => (
    <Card key={r.id} className="pushkin-card">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h3 className="font-semibold text-lg">{r.full_name}</h3>
              <Badge className="bg-amber-100 text-amber-800">
                {isOrganization(r) ? "Организация" : ROLE_LABELS[r.role] || r.role}
              </Badge>
            </div>
            {r.organization && <p className="text-sm"><strong>Организация:</strong> {r.organization}</p>}
            {r.position && <p className="text-sm"><strong>Должность:</strong> {r.position}</p>}
            <p className="text-sm text-muted-foreground mt-1">
              {r.email} · {r.phone} · @{r.username}
            </p>
            {r.verification_note && (
              <pre className="text-xs mt-3 p-3 rounded-lg bg-muted whitespace-pre-wrap">{r.verification_note}</pre>
            )}
            <p className="text-xs text-muted-foreground mt-2">{formatDate(r.created_at)}</p>
          </div>
          <div className="flex flex-col gap-2 shrink-0">
            <Button size="sm" onClick={() => handleUser(r.id, "approve")} disabled={loading === r.id}>
              ✓ Одобрить
            </Button>
            <Button size="sm" variant="destructive" onClick={() => handleUser(r.id, "reject")} disabled={loading === r.id}>
              ✗ Отклонить
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Модерация регистраций</h2>
        <p className="text-muted-foreground">
          Организации, службы, мастера — проверяйте данные перед публикацией на портале.
        </p>
      </div>

      <div className="pushkin-card p-4">
        <label className="text-sm font-medium">Причина отклонения (необязательно)</label>
        <input
          className="w-full mt-1 border rounded px-3 py-2 text-sm"
          placeholder="Например: не подтверждён адрес организации"
          value={rejectNote}
          onChange={(e) => setRejectNote(e.target.value)}
        />
      </div>

      <section>
        <h3 className="text-xl font-semibold mb-4">🏢 Организации ({organizations.length})</h3>
        {organizations.length === 0 ? (
          <p className="text-muted-foreground text-sm">Нет заявок</p>
        ) : (
          <div className="space-y-4">{organizations.map(renderUserCard)}</div>
        )}
      </section>

      <section>
        <h3 className="text-xl font-semibold mb-4">💇 Мастера услуг ({providers.length})</h3>
        {providers.length === 0 ? (
          <p className="text-muted-foreground text-sm">Нет заявок</p>
        ) : (
          <div className="space-y-4">
            {providers.map((p) => (
              <Card key={p.id} className="pushkin-card">
                <CardContent className="p-6 flex flex-wrap justify-between items-start gap-4">
                  <div>
                    <h4 className="font-semibold">{p.full_name}</h4>
                    <p className="text-sm text-muted-foreground">{p.phone} · {p.address}</p>
                    <p className="text-sm">{p.services.join(", ")}</p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button size="sm" onClick={() => handleProvider(p.id, "approve")} disabled={loading === p.id}>
                      ✓ Одобрить
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => handleProvider(p.id, "reject")} disabled={loading === p.id}>
                      ✗ Отклонить
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 className="text-xl font-semibold mb-4">🏛 Службы и администрация ({officials.length})</h3>
        {officials.length === 0 ? (
          <Card><CardContent className="py-8 text-center text-muted-foreground">Нет заявок</CardContent></Card>
        ) : (
          <div className="space-y-4">{officials.map(renderUserCard)}</div>
        )}
      </section>
    </div>
  );
}

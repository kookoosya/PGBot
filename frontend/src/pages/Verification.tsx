import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, VerificationRequest } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const ROLE_LABELS: Record<string, string> = {
  administration: "Администрация",
  social_service: "Соцслужбы",
  moderator: "Модератор",
};

export function Verification() {
  const [requests, setRequests] = useState<VerificationRequest[]>([]);
  const [loading, setLoading] = useState<number | null>(null);

  const load = () => api.getPendingVerifications().then(setRequests).catch(console.error);
  useEffect(() => { load(); }, []);

  const handle = async (id: number, action: "approve" | "reject") => {
    setLoading(id);
    try {
      if (action === "approve") await api.approveVerification(id);
      else await api.rejectVerification(id, "Не подтверждены данные");
      load();
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Верификация</h2>
        <p className="text-muted-foreground">Заявки на регистрацию служб и администрации</p>
      </div>

      {requests.length === 0 ? (
        <Card><CardContent className="py-12 text-center text-muted-foreground">
          Нет ожидающих заявок
        </CardContent></Card>
      ) : (
        <div className="space-y-4">
          {requests.map((r) => (
            <Card key={r.id} className="pushkin-card">
              <CardContent className="p-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">{r.full_name}</h3>
                      <Badge className="bg-amber-100 text-amber-800">
                        {ROLE_LABELS[r.role] || r.role}
                      </Badge>
                    </div>
                    <p className="text-sm"><strong>Организация:</strong> {r.organization}</p>
                    <p className="text-sm"><strong>Должность:</strong> {r.position}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {r.email} · {r.phone} · @{r.username}
                    </p>
                    {r.verification_note && (
                      <p className="text-sm mt-2 italic">«{r.verification_note}»</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">{formatDate(r.created_at)}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handle(r.id, "approve")}
                      disabled={loading === r.id}
                    >
                      ✓ Одобрить
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handle(r.id, "reject")}
                      disabled={loading === r.id}
                    >
                      ✗ Отклонить
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

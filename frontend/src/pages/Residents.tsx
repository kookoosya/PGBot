import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, User } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export function Residents() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    api.getUsers().then(setUsers).catch(console.error);
  }, []);

  const residents = users.filter((u) => u.role === "resident");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Жители</h2>
        <p className="text-muted-foreground">Жители с сайта и VK-бота</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="p-4 text-left font-medium">ID</th>
                <th className="p-4 text-left font-medium">Имя</th>
                <th className="p-4 text-left font-medium">Логин</th>
                <th className="p-4 text-left font-medium">Статус</th>
                <th className="p-4 text-left font-medium">Дата регистрации</th>
              </tr>
            </thead>
            <tbody>
              {residents.map((user) => (
                <tr key={user.id} className="border-b">
                  <td className="p-4">{user.id}</td>
                  <td className="p-4">{user.full_name || "—"}</td>
                  <td className="p-4">{user.username}</td>
                  <td className="p-4">
                    <Badge className={user.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                      {user.is_active ? "Активен" : "Неактивен"}
                    </Badge>
                  </td>
                  <td className="p-4 text-muted-foreground">{formatDate(user.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {residents.length === 0 && (
            <p className="text-center text-muted-foreground py-8">Жители не найдены</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

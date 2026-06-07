import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, Department } from "@/lib/api";

export function Departments() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const load = () => api.getDepartments().then(setDepartments).catch(console.error);
  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.createDepartment({ name, description });
    setName("");
    setDescription("");
    setShowForm(false);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Отделы</h2>
          <p className="text-muted-foreground">Ответственные подразделения</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "Добавить отдел"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleCreate} className="flex gap-3">
              <Input placeholder="Название" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input placeholder="Описание" value={description} onChange={(e) => setDescription(e.target.value)} />
              <Button type="submit">Создать</Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {departments.map((dept) => (
          <Card key={dept.id}>
            <CardHeader>
              <CardTitle className="text-lg">{dept.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{dept.description || "—"}</p>
              {dept.contact_email && (
                <p className="text-xs mt-2">📧 {dept.contact_email}</p>
              )}
              {dept.contact_phone && (
                <p className="text-xs">📞 {dept.contact_phone}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
